from __future__ import annotations

import base64
import hashlib
import io
import logging
import time

import cv2
import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageOps

from core.enums import EstadoProceso, ProveedorIA
from core.excepciones import ErrorDeDominio
from imagenes.models import FotoOriginal, ResultadoRecorte
from imagenes.services.servicio_gemini import ServicioGemini
from sesiones.services.servicio_sesiones import ServicioSesiones

logger = logging.getLogger(__name__)


class ServicioRecorteImagen:
    FORMATOS_PERMITIDOS = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }

    @staticmethod
    def obtener_foto(*, foto_id) -> FotoOriginal:
        try:
            return FotoOriginal.objects.select_related("sesion").get(id=foto_id)
        except FotoOriginal.DoesNotExist as exc:
            raise ErrorDeDominio(
                "No se encontro la foto solicitada.",
                codigo="foto_no_encontrada",
                estado_http=404,
            ) from exc

    @staticmethod
    def _leer_y_validar_archivo(archivo) -> tuple[bytes, dict]:
        contenido = archivo.read()
        if not contenido:
            raise ErrorDeDominio("El archivo enviado esta vacio.", codigo="archivo_vacio")

        tamano_maximo = settings.MAX_TAMANO_IMAGEN_MB * 1024 * 1024
        if len(contenido) > tamano_maximo:
            raise ErrorDeDominio(
                "La imagen supera el tamano maximo permitido.",
                codigo="imagen_demasiado_grande",
                campos={"tamano_maximo_mb": settings.MAX_TAMANO_IMAGEN_MB},
            )

        try:
            imagen = Image.open(io.BytesIO(contenido))
            imagen.load()
        except Exception as exc:
            raise ErrorDeDominio(
                "El archivo no corresponde a una imagen valida.",
                codigo="imagen_invalida",
            ) from exc

        formato = (imagen.format or "").upper()
        mime_type = ServicioRecorteImagen.FORMATOS_PERMITIDOS.get(formato)
        if not mime_type:
            raise ErrorDeDominio(
                "El formato de imagen no esta permitido. Usa JPEG, PNG o WEBP.",
                codigo="formato_no_permitido",
                campos={"formatos_permitidos": list(ServicioRecorteImagen.FORMATOS_PERMITIDOS)},
            )

        imagen_normalizada = ImageOps.exif_transpose(imagen)
        ancho, alto = imagen_normalizada.size
        if ancho < settings.MIN_ANCHO_IMAGEN or alto < settings.MIN_ALTO_IMAGEN:
            raise ErrorDeDominio(
                "La imagen no cumple con las dimensiones minimas requeridas.",
                codigo="dimensiones_insuficientes",
                campos={
                    "ancho_minimo": settings.MIN_ANCHO_IMAGEN,
                    "alto_minimo": settings.MIN_ALTO_IMAGEN,
                },
            )

        return contenido, {
            "mime_type": mime_type,
            "tamano_bytes": len(contenido),
            "ancho": ancho,
            "alto": alto,
            "hash_archivo": hashlib.sha256(contenido).hexdigest(),
            "formato": formato,
        }

    @staticmethod
    @transaction.atomic
    def guardar_foto_original(*, sesion, archivo) -> FotoOriginal:
        ServicioSesiones.validar_carga_habilitada(sesion)
        if sesion.fotos.filter(
            estado__in=[EstadoProceso.PENDIENTE, EstadoProceso.PROCESANDO]
        ).exists():
            raise ErrorDeDominio(
                "Ya existe una foto pendiente o en procesamiento para esta sesion.",
                codigo="foto_activa_existente",
                estado_http=409,
            )

        contenido, metadata = ServicioRecorteImagen._leer_y_validar_archivo(archivo)
        foto = FotoOriginal(
            sesion=sesion,
            nombre_original=archivo.name,
            mime_type=metadata["mime_type"],
            tamano_bytes=metadata["tamano_bytes"],
            ancho=metadata["ancho"],
            alto=metadata["alto"],
            hash_archivo=metadata["hash_archivo"],
            estado=EstadoProceso.PENDIENTE,
            metadata={"formato": metadata["formato"]},
        )
        foto.archivo.save(archivo.name, ContentFile(contenido), save=False)
        foto.save()
        ServicioSesiones.sincronizar_estado_proceso(sesion=sesion)
        return foto

    @staticmethod
    @transaction.atomic
    def preparar_procesamiento(*, foto: FotoOriginal) -> tuple[ResultadoRecorte, bool]:
        foto_bloqueada = (
            FotoOriginal.objects.select_for_update()
            .select_related("sesion")
            .get(id=foto.id)
        )
        ServicioSesiones.validar_carga_habilitada(foto_bloqueada.sesion)

        if FotoOriginal.objects.filter(
            sesion=foto_bloqueada.sesion,
            estado__in=[EstadoProceso.PENDIENTE, EstadoProceso.PROCESANDO],
        ).exclude(id=foto_bloqueada.id).exists():
            raise ErrorDeDominio(
                "La sesion ya tiene otra foto en cola o procesandose.",
                codigo="sesion_con_proceso_activo",
                estado_http=409,
            )

        resultado, creado = ResultadoRecorte.objects.select_for_update().get_or_create(
            foto_original=foto_bloqueada,
            defaults={
                "estado": EstadoProceso.PENDIENTE,
                "proveedor_ia": ProveedorIA.GEMINI,
            },
        )

        if not creado and resultado.estado in [EstadoProceso.PENDIENTE, EstadoProceso.PROCESANDO]:
            raise ErrorDeDominio(
                "Esta foto ya tiene un procesamiento activo.",
                codigo="procesamiento_duplicado",
                estado_http=409,
            )

        if not creado and resultado.estado == EstadoProceso.COMPLETADO:
            return resultado, True

        resultado.estado = EstadoProceso.PENDIENTE
        resultado.errores = ""
        resultado.metadatos_recorte = {}
        resultado.celery_task_id = ""
        resultado.tiempo_procesamiento = None
        resultado.fecha_inicio_procesamiento = None
        resultado.fecha_fin_procesamiento = None
        resultado.save()
        return resultado, False

    @staticmethod
    def registrar_tarea(*, resultado: ResultadoRecorte, task_id: str) -> ResultadoRecorte:
        resultado.celery_task_id = task_id
        resultado.save(update_fields=["celery_task_id", "actualizado_en"])
        return resultado

    @staticmethod
    def _abrir_imagen_normalizada(contenido: bytes) -> Image.Image:
        imagen = Image.open(io.BytesIO(contenido))
        imagen = ImageOps.exif_transpose(imagen)
        return imagen.convert("RGBA")

    @staticmethod
    def _seleccionar_segmento_persona(segmentos: list[dict]) -> dict:
        candidatos = [
            segmento
            for segmento in segmentos
            if "person" in segmento["label"] or "persona" in segmento["label"]
        ]
        if not candidatos:
            raise ErrorDeDominio(
                "Gemini no detecto una persona utilizable en la imagen.",
                codigo="persona_no_detectada",
                estado_http=422,
            )

        def area(segmento):
            y0, x0, y1, x1 = segmento["box_2d"]
            return max(y1 - y0, 0) * max(x1 - x0, 0)

        return max(candidatos, key=area)

    @staticmethod
    def _reconstruir_mascara(segmento: dict, ancho: int, alto: int) -> np.ndarray:
        y0, x0, y1, x1 = [int(round(float(valor))) for valor in segmento["box_2d"]]
        x0 = max(0, min(ancho - 1, int(x0 * ancho / 1000)))
        x1 = max(0, min(ancho, int(x1 * ancho / 1000)))
        y0 = max(0, min(alto - 1, int(y0 * alto / 1000)))
        y1 = max(0, min(alto, int(y1 * alto / 1000)))
        if x1 <= x0 or y1 <= y0:
            raise ErrorDeDominio(
                "Gemini devolvio un bounding box invalido.",
                codigo="bbox_invalido",
                estado_http=502,
            )

        mascara_bytes = base64.b64decode(segmento["mask"])
        imagen_mascara = Image.open(io.BytesIO(mascara_bytes)).convert("L")
        mascara_local = cv2.resize(
            np.array(imagen_mascara),
            (x1 - x0, y1 - y0),
            interpolation=cv2.INTER_LINEAR,
        )
        mascara_binaria = np.where(mascara_local >= 127, 255, 0).astype(np.uint8)
        mascara_completa = np.zeros((alto, ancho), dtype=np.uint8)
        mascara_completa[y0:y1, x0:x1] = mascara_binaria
        return mascara_completa

    @staticmethod
    def _refinar_mascara(mascara: np.ndarray) -> np.ndarray:
        kernel = np.ones((3, 3), np.uint8)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel, iterations=2)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel, iterations=1)
        mascara = cv2.GaussianBlur(mascara, (0, 0), sigmaX=1.2)
        return mascara

    @staticmethod
    def _renderizar_recorte(
        imagen: Image.Image, mascara: np.ndarray
    ) -> tuple[bytes, bytes, dict]:
        alfa = Image.fromarray(mascara, mode="L")
        imagen_rgba = imagen.copy()
        imagen_rgba.putalpha(alfa)
        indices = np.argwhere(mascara > 10)
        if indices.size == 0:
            raise ErrorDeDominio(
                "No fue posible construir una mascara de persona valida.",
                codigo="mascara_vacia",
                estado_http=422,
            )

        y0, x0 = indices.min(axis=0)
        y1, x1 = indices.max(axis=0)
        margen = 20
        caja = (
            max(x0 - margen, 0),
            max(y0 - margen, 0),
            min(x1 + margen, imagen.width),
            min(y1 + margen, imagen.height),
        )
        recorte = imagen_rgba.crop(caja)
        mascara_recortada = alfa.crop(caja)

        buffer_recorte = io.BytesIO()
        buffer_mascara = io.BytesIO()
        recorte.save(buffer_recorte, format="PNG")
        mascara_recortada.save(buffer_mascara, format="PNG")
        return buffer_recorte.getvalue(), buffer_mascara.getvalue(), {
            "caja": [int(valor) for valor in caja]
        }

    @staticmethod
    def marcar_error(*, foto_id, mensaje: str) -> None:
        try:
            foto = FotoOriginal.objects.select_related("sesion").get(id=foto_id)
        except FotoOriginal.DoesNotExist:
            return

        foto.estado = EstadoProceso.ERROR
        foto.mensaje_error = mensaje
        foto.save(update_fields=["estado", "mensaje_error", "actualizado_en"])
        ResultadoRecorte.objects.filter(foto_original=foto).update(
            estado=EstadoProceso.ERROR,
            errores=mensaje,
            fecha_fin_procesamiento=timezone.now(),
        )
        ServicioSesiones.sincronizar_estado_proceso(sesion=foto.sesion)

    @staticmethod
    def procesar_foto(*, foto_id, plantilla_id=None, task_id: str | None = None):
        inicio = time.perf_counter()
        with transaction.atomic():
            foto = FotoOriginal.objects.select_for_update().select_related("sesion").get(id=foto_id)
            resultado = ResultadoRecorte.objects.select_for_update().get(foto_original=foto)
            foto.estado = EstadoProceso.PROCESANDO
            foto.mensaje_error = ""
            foto.save(update_fields=["estado", "mensaje_error", "actualizado_en"])
            resultado.estado = EstadoProceso.PROCESANDO
            resultado.proveedor_ia = ProveedorIA.GEMINI
            resultado.fecha_inicio_procesamiento = timezone.now()
            if task_id:
                resultado.celery_task_id = task_id
            resultado.errores = ""
            resultado.save(
                update_fields=[
                    "estado",
                    "proveedor_ia",
                    "fecha_inicio_procesamiento",
                    "celery_task_id",
                    "errores",
                    "actualizado_en",
                ]
            )

        with foto.archivo.open("rb") as descriptor:
            contenido = descriptor.read()

        imagen = ServicioRecorteImagen._abrir_imagen_normalizada(contenido)
        servicio_gemini = ServicioGemini()
        analisis = servicio_gemini.analizar_persona(contenido, foto.mime_type)
        segmento = ServicioRecorteImagen._seleccionar_segmento_persona(analisis["segmentos"])
        mascara = ServicioRecorteImagen._reconstruir_mascara(
            segmento, imagen.width, imagen.height
        )
        mascara_refinada = ServicioRecorteImagen._refinar_mascara(mascara)
        recorte_bytes, mascara_bytes, metadata_render = ServicioRecorteImagen._renderizar_recorte(
            imagen, mascara_refinada
        )

        with transaction.atomic():
            foto = FotoOriginal.objects.select_for_update().select_related("sesion").get(id=foto_id)
            resultado = ResultadoRecorte.objects.select_for_update().get(foto_original=foto)
            resultado.png_transparente.save(
                f"recorte_{foto.id}.png", ContentFile(recorte_bytes), save=False
            )
            resultado.archivo_mascara.save(
                f"mascara_{foto.id}.png", ContentFile(mascara_bytes), save=False
            )
            resultado.estado = EstadoProceso.COMPLETADO
            resultado.modelo_gemini = analisis["modelo"]
            resultado.metadatos_recorte = {
                "segmento_seleccionado": {
                    "label": segmento["label"],
                    "box_2d": segmento["box_2d"],
                },
                "metadata_render": metadata_render,
                "gemini": {
                    "modelo": analisis["modelo"],
                    "cantidad_segmentos": len(analisis["segmentos"]),
                },
            }
            resultado.tiempo_procesamiento = round(time.perf_counter() - inicio, 3)
            resultado.fecha_fin_procesamiento = timezone.now()
            resultado.errores = ""
            resultado.save()

            foto.estado = EstadoProceso.COMPLETADO
            foto.mensaje_error = ""
            foto.save(update_fields=["estado", "mensaje_error", "actualizado_en"])

        from figuritas.services.servicio_composicion_figurita import ServicioComposicionFigurita

        ServicioSesiones.sincronizar_estado_proceso(sesion=foto.sesion)
        ServicioComposicionFigurita.generar_automaticamente_si_corresponde(
            resultado_recorte_id=resultado.id,
            plantilla_id=plantilla_id,
        )
        logger.info("Procesamiento completado", extra={"foto_id": str(foto_id)})
        return resultado
