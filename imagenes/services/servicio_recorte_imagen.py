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
    def _detectar_rostro_principal(imagen_bgr: np.ndarray) -> tuple[int, int, int, int] | None:
        gris = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)
        clasificador = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if clasificador.empty():
            return None

        alto, ancho = gris.shape[:2]
        min_lado = max(80, min(ancho, alto) // 12)
        detecciones = clasificador.detectMultiScale(
            gris,
            scaleFactor=1.08,
            minNeighbors=5,
            minSize=(min_lado, min_lado),
        )
        if len(detecciones) == 0:
            return None

        centro_imagen_x = ancho / 2

        def puntaje(rostro):
            x, y, w, h = [int(valor) for valor in rostro]
            area = w * h
            centro_rostro_x = x + (w / 2)
            penalizacion_centro = abs(centro_rostro_x - centro_imagen_x) * 0.35
            penalizacion_altura = y * 0.08
            return area - penalizacion_centro - penalizacion_altura

        mejor = max(detecciones, key=puntaje)
        return tuple(int(valor) for valor in mejor)

    @staticmethod
    def _construir_silueta_busto_desde_rostro(
        shape: tuple[int, int], rostro: tuple[int, int, int, int]
    ) -> np.ndarray:
        alto, ancho = shape
        silueta = np.zeros((alto, ancho), dtype=np.uint8)
        x, y, w, h = rostro
        centro_x = int(x + (w / 2))

        centro_cabeza = (centro_x, int(y + (h * 0.58)))
        ejes_cabeza = (
            max(int(w * 0.98), 18),
            max(int(h * 1.04), 24),
        )
        cv2.ellipse(silueta, centro_cabeza, ejes_cabeza, 0, 0, 360, 255, -1)

        cuello_x0 = max(int(centro_x - (w * 0.45)), 0)
        cuello_x1 = min(int(centro_x + (w * 0.45)), ancho)
        cuello_y0 = max(int(y + (h * 0.92)), 0)
        cuello_y1 = min(int(y + (h * 1.85)), alto)
        silueta[cuello_y0:cuello_y1, cuello_x0:cuello_x1] = 255

        hombros_centro_y = min(int(y + (h * 2.32)), alto - 1)
        hombros_ancho = max(int(w * 1.55), 34)
        hombros_alto = max(int(h * 0.96), 28)
        cv2.ellipse(
            silueta,
            (centro_x, hombros_centro_y),
            (hombros_ancho, hombros_alto),
            0,
            0,
            360,
            255,
            -1,
        )

        torso_x0 = max(int(centro_x - (w * 1.16)), 0)
        torso_x1 = min(int(centro_x + (w * 1.16)), ancho)
        torso_y0 = max(int(y + (h * 1.42)), 0)
        torso_y1 = min(int(y + (h * 3.2)), alto)
        silueta[torso_y0:torso_y1, torso_x0:torso_x1] = 255

        silueta = cv2.GaussianBlur(silueta, (0, 0), sigmaX=2.0)
        return silueta

    @staticmethod
    def _muestrear_fondo_desde_bordes(imagen_bgr: np.ndarray) -> tuple[np.ndarray, float, float]:
        alto, ancho = imagen_bgr.shape[:2]
        margen = max(min(ancho, alto) // 20, 18)
        muestras = [
            imagen_bgr[:margen, :, :],
            imagen_bgr[:, :margen, :],
            imagen_bgr[:, max(ancho - margen, 0) :, :],
            imagen_bgr[max(alto - margen, 0) :, : max(margen * 2, 1), :],
            imagen_bgr[max(alto - margen, 0) :, max(ancho - (margen * 2), 0) :, :],
        ]
        muestras = [muestra.reshape(-1, 3) for muestra in muestras if muestra.size]
        if not muestras:
            return np.array([0.0, 0.0, 0.0], dtype=np.float32), 18.0, 38.0

        muestras_np = np.concatenate(muestras, axis=0)
        muestras_lab = cv2.cvtColor(
            muestras_np.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB
        ).reshape(-1, 3)
        color_fondo = np.median(muestras_lab, axis=0).astype(np.float32)
        distancias = np.linalg.norm(muestras_lab - color_fondo, axis=1)
        umbral_bajo = max(float(np.percentile(distancias, 92)) + 5.0, 16.0)
        umbral_alto = max(umbral_bajo + 18.0, 34.0)
        return color_fondo, umbral_bajo, umbral_alto

    @staticmethod
    def _seleccionar_componente_rostro(
        mascara: np.ndarray,
        rostro: tuple[int, int, int, int],
    ) -> np.ndarray:
        num_etiquetas, etiquetas, estadisticas, _ = cv2.connectedComponentsWithStats(mascara)
        if num_etiquetas <= 1:
            return mascara

        x, y, w, h = rostro
        x0 = max(int(x - (w * 0.2)), 0)
        y0 = max(int(y - (h * 0.2)), 0)
        x1 = min(int(x + w + (w * 0.2)), mascara.shape[1])
        y1 = min(int(y + h + (h * 0.2)), mascara.shape[0])

        mejor_etiqueta = None
        mejor_area = 0
        for etiqueta in range(1, num_etiquetas):
            area = int(estadisticas[etiqueta, cv2.CC_STAT_AREA])
            if area <= mejor_area:
                continue
            mascara_etiqueta = etiquetas == etiqueta
            if np.any(mascara_etiqueta[y0:y1, x0:x1]):
                mejor_etiqueta = etiqueta
                mejor_area = area

        if mejor_etiqueta is None:
            mejor_etiqueta = int(1 + np.argmax(estadisticas[1:, cv2.CC_STAT_AREA]))

        resultado = np.zeros_like(mascara)
        resultado[etiquetas == mejor_etiqueta] = 255
        return resultado

    @staticmethod
    def _acotar_mascara_a_busto(imagen: Image.Image, mascara: np.ndarray) -> np.ndarray:
        imagen_bgr = cv2.cvtColor(np.array(imagen.convert("RGB")), cv2.COLOR_RGB2BGR)
        rostro = ServicioRecorteImagen._detectar_rostro_principal(imagen_bgr)
        if rostro is None:
            return mascara

        x, y, w, h = rostro
        silueta_busto = ServicioRecorteImagen._construir_silueta_busto_desde_rostro(
            mascara.shape,
            rostro,
        )
        color_fondo, umbral_bajo, umbral_alto = (
            ServicioRecorteImagen._muestrear_fondo_desde_bordes(imagen_bgr)
        )
        imagen_lab = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
        distancia = np.linalg.norm(imagen_lab - color_fondo, axis=2)
        color_fondo_probable = np.clip(
            (distancia - umbral_bajo) / max(umbral_alto - umbral_bajo, 1.0),
            0.0,
            1.0,
        )
        color_fondo_probable = (color_fondo_probable * 255).astype(np.uint8)

        alto, ancho = mascara.shape
        mascara_gc = np.full((alto, ancho), cv2.GC_PR_BGD, dtype=np.uint8)
        margen_borde = max(min(ancho, alto) // 32, 14)
        mascara_gc[:margen_borde, :] = cv2.GC_BGD
        mascara_gc[:, :margen_borde] = cv2.GC_BGD
        mascara_gc[:, max(ancho - margen_borde, 0) :] = cv2.GC_BGD
        mascara_gc[max(alto - margen_borde, 0) :, :] = cv2.GC_BGD

        mascara_gc[silueta_busto <= 8] = cv2.GC_BGD
        mascara_gc[mascara >= 72] = cv2.GC_PR_FGD
        mascara_gc[color_fondo_probable >= 168] = cv2.GC_PR_FGD
        mascara_gc[(color_fondo_probable <= 28) & (silueta_busto <= 32)] = cv2.GC_BGD

        rostro_y0 = max(int(y - (h * 0.28)), 0)
        rostro_y1 = min(int(y + h + (h * 0.18)), alto)
        rostro_x0 = max(int(x - (w * 0.18)), 0)
        rostro_x1 = min(int(x + w + (w * 0.18)), ancho)
        mascara_gc[rostro_y0:rostro_y1, rostro_x0:rostro_x1] = cv2.GC_FGD

        torso_y0 = min(int(y + (h * 0.95)), alto)
        torso_y1 = min(int(y + (h * 2.85)), alto)
        torso_x0 = max(int((x + (w / 2)) - (w * 0.92)), 0)
        torso_x1 = min(int((x + (w / 2)) + (w * 0.92)), ancho)
        if torso_y1 > torso_y0 and torso_x1 > torso_x0:
            region_torso = mascara_gc[torso_y0:torso_y1, torso_x0:torso_x1]
            region_torso[:] = np.maximum(region_torso, cv2.GC_PR_FGD)

        fondo_modelo = np.zeros((1, 65), np.float64)
        primer_plano_modelo = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(
                imagen_bgr,
                mascara_gc,
                None,
                fondo_modelo,
                primer_plano_modelo,
                3,
                cv2.GC_INIT_WITH_MASK,
            )
            refinada = np.where(
                (mascara_gc == cv2.GC_FGD) | (mascara_gc == cv2.GC_PR_FGD),
                255,
                0,
            ).astype(np.uint8)
        except cv2.error:
            refinada = cv2.min(mascara.astype(np.uint8), color_fondo_probable)

        limpieza_color = np.where(color_fondo_probable >= 52, 255, 0).astype(np.uint8)
        limpieza_color[rostro_y0:rostro_y1, rostro_x0:rostro_x1] = 255
        if torso_y1 > torso_y0 and torso_x1 > torso_x0:
            limpieza_color[torso_y0:torso_y1, torso_x0:torso_x1] = 255

        refinada = cv2.bitwise_and(refinada, silueta_busto)
        refinada = cv2.bitwise_and(refinada, limpieza_color)
        refinada = ServicioRecorteImagen._seleccionar_componente_rostro(refinada, rostro)
        refinada = cv2.morphologyEx(
            refinada,
            cv2.MORPH_CLOSE,
            np.ones((5, 5), np.uint8),
            iterations=2,
        )
        refinada = cv2.morphologyEx(
            refinada,
            cv2.MORPH_OPEN,
            np.ones((3, 3), np.uint8),
            iterations=1,
        )
        refinada = cv2.GaussianBlur(refinada, (0, 0), sigmaX=1.5)
        return refinada

    @staticmethod
    def _normalizar_alpha(mascara: np.ndarray, umbral: int = 20) -> np.ndarray:
        alpha = mascara.astype(np.uint8).copy()
        alpha[alpha < umbral] = 0
        alpha[alpha > 245] = 255
        return alpha

    @staticmethod
    def _seleccionar_mayor_componente(mascara: np.ndarray, umbral: int = 20) -> np.ndarray:
        mascara_binaria = np.where(mascara > umbral, 255, 0).astype(np.uint8)
        num_etiquetas, etiquetas, estadisticas, _ = cv2.connectedComponentsWithStats(
            mascara_binaria
        )
        if num_etiquetas <= 1:
            return mascara_binaria
        etiqueta_principal = int(1 + np.argmax(estadisticas[1:, cv2.CC_STAT_AREA]))
        resultado = np.zeros_like(mascara_binaria)
        resultado[etiquetas == etiqueta_principal] = 255
        return resultado

    @staticmethod
    def _obtener_caja_alpha(mascara: np.ndarray, umbral: int = 20) -> tuple[int, int, int, int] | None:
        indices = np.argwhere(mascara > umbral)
        if indices.size == 0:
            return None
        y0, x0 = indices.min(axis=0)
        y1, x1 = indices.max(axis=0)
        return int(x0), int(y0), int(x1) + 1, int(y1) + 1

    @staticmethod
    def _renderizar_recorte(
        imagen: Image.Image, mascara: np.ndarray
    ) -> tuple[bytes, bytes, dict]:
        mascara_limpia = ServicioRecorteImagen._normalizar_alpha(mascara)
        mascara_principal = ServicioRecorteImagen._seleccionar_mayor_componente(
            mascara_limpia,
            umbral=20,
        )
        mascara_limpia = cv2.bitwise_and(mascara_limpia, mascara_principal)
        alfa = Image.fromarray(mascara_limpia, mode="L")
        imagen_rgba = imagen.copy()
        imagen_rgba.putalpha(alfa)
        caja_alpha = ServicioRecorteImagen._obtener_caja_alpha(mascara_limpia)
        if not caja_alpha:
            raise ErrorDeDominio(
                "No fue posible construir una mascara de persona valida.",
                codigo="mascara_vacia",
                estado_http=422,
            )

        x0, y0, x1, y1 = caja_alpha
        margen = 20
        caja = (
            max(x0 - margen, 0),
            max(y0 - margen, 0),
            min(x1 + margen, imagen.width),
            min(y1 + margen, imagen.height),
        )
        recorte = imagen_rgba.crop(caja)
        mascara_recortada = alfa.crop(caja)

        caja_local = ServicioRecorteImagen._obtener_caja_alpha(
            np.array(mascara_recortada), umbral=20
        )
        if caja_local:
            recorte = recorte.crop(caja_local)
            mascara_recortada = mascara_recortada.crop(caja_local)

        buffer_recorte = io.BytesIO()
        buffer_mascara = io.BytesIO()
        recorte.save(buffer_recorte, format="PNG")
        mascara_recortada.save(buffer_mascara, format="PNG")
        return buffer_recorte.getvalue(), buffer_mascara.getvalue(), {
            "caja": [int(valor) for valor in caja],
            "caja_alpha_local": [int(valor) for valor in caja_local] if caja_local else None,
            "umbral_alpha": 20,
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
        try:
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
            mascara_refinada = ServicioRecorteImagen._acotar_mascara_a_busto(
                imagen,
                mascara_refinada,
            )
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
                    "fallback_local": bool(
                        analisis.get("respuesta_cruda", {}).get("fallback_local", False)
                    ),
                    "motivo_error_gemini": analisis.get("respuesta_cruda", {}).get(
                        "motivo_error"
                    ),
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
        except ErrorDeDominio as exc:
            ServicioRecorteImagen.marcar_error(
                foto_id=foto_id,
                mensaje=exc.mensaje,
            )
            raise
        except Exception as exc:
            ServicioRecorteImagen.marcar_error(
                foto_id=foto_id,
                mensaje="No fue posible completar el recorte de la imagen.",
            )
            raise ErrorDeDominio(
                "No fue posible completar el recorte de la imagen.",
                codigo="recorte_fallido",
                estado_http=500,
            ) from exc
