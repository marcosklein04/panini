from __future__ import annotations

import io
import logging

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from core.enums import EstadoProceso
from core.excepciones import ErrorDeDominio
from figuritas.models import FiguritaGenerada, PlantillaFigurita
from sesiones.services.servicio_sesiones import ServicioSesiones
from trivias.services.servicio_validacion_sticker import ServicioValidacionSticker

logger = logging.getLogger(__name__)


class ServicioComposicionFigurita:
    CONFIG_DEFAULT = {
        "ancho": 900,
        "alto": 1200,
        "color_fondo_inicio": "#0F6CBD",
        "color_fondo_fin": "#7BE0FF",
        "color_marco": "#F7D35B",
        "color_texto": "#FFFFFF",
        "color_texto_secundario": "#FFEAA0",
        "titulo_superior": "EDICION PERSONALIZADA",
        "subtitulo": "STICKER FAN CARD",
        "badge": "TITULAR",
        "escala_persona": 0.72,
        "desplazamiento_x": 0,
        "desplazamiento_y": 40,
    }

    @staticmethod
    def _obtener_plantilla(plantilla_id=None) -> PlantillaFigurita:
        consulta = PlantillaFigurita.objects.filter(activa=True)
        if plantilla_id:
            plantilla = consulta.filter(id=plantilla_id).first()
        else:
            plantilla = consulta.filter(predeterminada=True).first() or consulta.first()
        if not plantilla:
            raise ErrorDeDominio(
                "No hay una plantilla de figurita activa disponible.",
                codigo="plantilla_no_disponible",
                estado_http=404,
            )
        return plantilla

    @staticmethod
    def _obtener_datos_sticker(resultado_recorte):
        datos = getattr(resultado_recorte.foto_original.sesion, "datos_sticker", None)
        if not datos:
            raise ErrorDeDominio(
                "La sesion aun no tiene datos normalizados para renderizar la figurita.",
                codigo="datos_sticker_no_disponibles",
                estado_http=409,
            )
        evaluacion = ServicioValidacionSticker.evaluar_sesion(resultado_recorte.foto_original.sesion)
        if not evaluacion["es_completa"]:
            raise ErrorDeDominio(
                "Faltan datos obligatorios para generar la figurita.",
                codigo="datos_sticker_incompletos",
                estado_http=409,
                campos={"campos_faltantes": evaluacion["campos_faltantes"]},
            )
        return datos

    @staticmethod
    def _nombre_mostrado(datos_sticker) -> str:
        return f"{datos_sticker.nombre} {datos_sticker.apellido}".strip()

    @staticmethod
    def crear_registro_pendiente(*, resultado_recorte, plantilla_id=None) -> FiguritaGenerada:
        if resultado_recorte.estado != EstadoProceso.COMPLETADO:
            raise ErrorDeDominio(
                "El recorte aun no esta completado.",
                codigo="recorte_no_completado",
                estado_http=409,
            )
        plantilla = ServicioComposicionFigurita._obtener_plantilla(plantilla_id=plantilla_id)
        datos_sticker = ServicioComposicionFigurita._obtener_datos_sticker(resultado_recorte)
        return FiguritaGenerada.objects.create(
            sesion=resultado_recorte.foto_original.sesion,
            resultado_recorte=resultado_recorte,
            plantilla=plantilla,
            estado=EstadoProceso.PENDIENTE,
            nombre_mostrado=ServicioComposicionFigurita._nombre_mostrado(datos_sticker),
        )

    @staticmethod
    def registrar_tarea(*, figurita: FiguritaGenerada, task_id: str):
        figurita.celery_task_id = task_id
        figurita.save(update_fields=["celery_task_id", "actualizado_en"])
        return figurita

    @staticmethod
    def _cargar_fuente(tamano: int, negrita: bool = False):
        candidatos = [
            "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf",
            "Arial.ttf",
        ]
        for nombre in candidatos:
            try:
                return ImageFont.truetype(nombre, tamano)
            except OSError:
                continue
        return ImageFont.load_default()

    @staticmethod
    def _crear_fondo(configuracion: dict, plantilla: PlantillaFigurita) -> Image.Image:
        ancho = configuracion["ancho"]
        alto = configuracion["alto"]
        if plantilla.archivo_base:
            with plantilla.archivo_base.open("rb") as descriptor:
                fondo = Image.open(descriptor).convert("RGBA")
                return fondo.resize((ancho, alto))

        color_inicio = configuracion["color_fondo_inicio"]
        color_fin = configuracion["color_fondo_fin"]
        fondo = Image.new("RGBA", (ancho, alto), color_inicio)
        dibujo = ImageDraw.Draw(fondo)
        for y in range(alto):
            proporcion = y / max(alto - 1, 1)
            color = _interpolar_color(color_inicio, color_fin, proporcion)
            dibujo.line([(0, y), (ancho, y)], fill=color)
        return fondo

    @staticmethod
    def marcar_error(*, figurita_id, mensaje: str):
        figurita = FiguritaGenerada.objects.filter(id=figurita_id).first()
        if not figurita:
            return
        FiguritaGenerada.objects.filter(id=figurita_id).update(
            estado=EstadoProceso.ERROR,
            mensaje_error=mensaje,
            fecha_generacion=timezone.now(),
        )
        ServicioSesiones.sincronizar_estado_proceso(sesion=figurita.sesion)

    @staticmethod
    def obtener_figurita_publica(*, figurita_id) -> FiguritaGenerada:
        try:
            return FiguritaGenerada.objects.select_related(
                "sesion",
                "plantilla",
                "resultado_recorte",
                "resultado_recorte__foto_original",
            ).get(id=figurita_id)
        except FiguritaGenerada.DoesNotExist as exc:
            raise ErrorDeDominio(
                "No se encontro la figurita solicitada.",
                codigo="figurita_no_encontrada",
                estado_http=404,
            ) from exc

    @staticmethod
    def generar_automaticamente_si_corresponde(*, resultado_recorte_id, plantilla_id=None):
        from figuritas.tasks import tarea_generar_figurita
        from imagenes.models import ResultadoRecorte

        resultado = ResultadoRecorte.objects.select_related(
            "foto_original",
            "foto_original__sesion",
            "foto_original__sesion__datos_sticker",
        ).get(id=resultado_recorte_id)
        try:
            figurita = ServicioComposicionFigurita.crear_registro_pendiente(
                resultado_recorte=resultado,
                plantilla_id=plantilla_id,
            )
        except ErrorDeDominio:
            return None
        if settings.CELERY_TASK_ALWAYS_EAGER:
            return ServicioComposicionFigurita.generar_figurita(figurita_id=str(figurita.id))
        tarea = tarea_generar_figurita.delay(str(figurita.id))
        ServicioComposicionFigurita.registrar_tarea(figurita=figurita, task_id=tarea.id)
        return figurita

    @staticmethod
    def generar_figurita(*, figurita_id: str, task_id: str | None = None) -> FiguritaGenerada:
        with transaction.atomic():
            figurita = (
                FiguritaGenerada.objects.select_for_update()
                .select_related(
                    "sesion",
                    "plantilla",
                    "resultado_recorte",
                    "resultado_recorte__foto_original",
                )
                .get(id=figurita_id)
            )
            figurita.estado = EstadoProceso.PROCESANDO
            figurita.mensaje_error = ""
            if task_id:
                figurita.celery_task_id = task_id
            figurita.save(
                update_fields=["estado", "mensaje_error", "celery_task_id", "actualizado_en"]
            )

        datos_sticker = ServicioComposicionFigurita._obtener_datos_sticker(
            figurita.resultado_recorte
        )
        config = {
            **ServicioComposicionFigurita.CONFIG_DEFAULT,
            **figurita.plantilla.configuracion_visual,
        }
        fondo = ServicioComposicionFigurita._crear_fondo(config, figurita.plantilla)
        ancho = config["ancho"]
        alto = config["alto"]

        with figurita.resultado_recorte.png_transparente.open("rb") as descriptor:
            persona = Image.open(descriptor).convert("RGBA")

        sombra = persona.copy()
        alfa_sombra = sombra.getchannel("A").filter(ImageFilter.GaussianBlur(radius=18))
        sombra.putalpha(alfa_sombra)

        escala = float(config["escala_persona"])
        max_alto_persona = int(alto * escala)
        proporcion = max_alto_persona / max(persona.height, 1)
        nuevo_tamano = (int(persona.width * proporcion), int(persona.height * proporcion))
        persona = persona.resize(nuevo_tamano, Image.Resampling.LANCZOS)
        sombra = sombra.resize(nuevo_tamano, Image.Resampling.LANCZOS)

        centro_x = ancho // 2 + int(config["desplazamiento_x"])
        base_y = alto - 120 + int(config["desplazamiento_y"])
        posicion_persona = (centro_x - persona.width // 2, base_y - persona.height)
        posicion_sombra = (posicion_persona[0] + 20, posicion_persona[1] + 25)
        fondo.alpha_composite(sombra, posicion_sombra)
        fondo.alpha_composite(persona, posicion_persona)

        dibujo = ImageDraw.Draw(fondo)
        dibujo.rounded_rectangle(
            [(32, 32), (ancho - 32, alto - 32)],
            radius=36,
            outline=config["color_marco"],
            width=10,
        )
        dibujo.rounded_rectangle(
            [(60, 60), (ancho - 60, 190)],
            radius=28,
            fill=(0, 0, 0, 120),
            outline=config["color_marco"],
            width=4,
        )
        dibujo.ellipse(
            [(ancho - 240, 210), (ancho - 90, 360)],
            fill=config["color_marco"],
            outline="white",
            width=3,
        )

        fuente_titulo = ServicioComposicionFigurita._cargar_fuente(48, negrita=True)
        fuente_subtitulo = ServicioComposicionFigurita._cargar_fuente(24, negrita=False)
        fuente_badge = ServicioComposicionFigurita._cargar_fuente(24, negrita=True)
        fuente_nombre = ServicioComposicionFigurita._cargar_fuente(42, negrita=True)
        fuente_info = ServicioComposicionFigurita._cargar_fuente(26, negrita=False)

        dibujo.text(
            (90, 82),
            str(config["titulo_superior"]),
            font=fuente_titulo,
            fill=config["color_texto"],
        )
        dibujo.text(
            (92, 138),
            str(config["subtitulo"]),
            font=fuente_subtitulo,
            fill=config["color_texto_secundario"],
        )
        dibujo.text(
            (ancho - 165, 267),
            str(config["badge"]),
            anchor="mm",
            font=fuente_badge,
            fill="#16354B",
        )

        nombre = ServicioComposicionFigurita._nombre_mostrado(datos_sticker).upper()
        dibujo.rounded_rectangle(
            [(80, alto - 245), (ancho - 80, alto - 80)],
            radius=24,
            fill=(0, 0, 0, 160),
            outline=config["color_marco"],
            width=4,
        )
        dibujo.text(
            (120, alto - 220),
            nombre,
            font=fuente_nombre,
            fill=config["color_texto"],
        )
        if datos_sticker.apodo:
            dibujo.text(
                (122, alto - 175),
                f'APODO: "{datos_sticker.apodo.upper()}"',
                font=fuente_info,
                fill=config["color_texto_secundario"],
            )
        dibujo.text(
            (122, alto - 140),
            f"NACIMIENTO: {datos_sticker.fecha_nacimiento.strftime('%d/%m/%Y')}",
            font=fuente_info,
            fill=config["color_texto_secundario"],
        )
        dibujo.text(
            (122, alto - 108),
            f"ALTURA: {datos_sticker.altura_cm} CM   PESO: {datos_sticker.peso_kg} KG",
            font=fuente_info,
            fill=config["color_texto_secundario"],
        )
        dibujo.text(
            (122, alto - 76),
            f"EQUIPO: {datos_sticker.equipo.upper()}",
            font=fuente_info,
            fill=config["color_texto_secundario"],
        )

        imagen_final = fondo.convert("RGB")
        preview = imagen_final.copy()
        preview.thumbnail((400, 400))

        buffer_final = io.BytesIO()
        buffer_preview = io.BytesIO()
        imagen_final.save(buffer_final, format="PNG")
        preview.save(buffer_preview, format="JPEG", quality=90)

        datos_renderizados = {
            "nombre": datos_sticker.nombre,
            "apellido": datos_sticker.apellido,
            "fecha_nacimiento": datos_sticker.fecha_nacimiento.isoformat(),
            "altura_cm": datos_sticker.altura_cm,
            "peso_kg": datos_sticker.peso_kg,
            "equipo": datos_sticker.equipo,
            "apodo": datos_sticker.apodo,
            "posicion": datos_sticker.posicion,
            "nacionalidad": datos_sticker.nacionalidad,
        }

        with transaction.atomic():
            figurita = FiguritaGenerada.objects.select_for_update().get(id=figurita_id)
            figurita.imagen_final.save(
                f"figurita_{figurita.id}.png", ContentFile(buffer_final.getvalue()), save=False
            )
            figurita.imagen_preview.save(
                f"preview_{figurita.id}.jpg", ContentFile(buffer_preview.getvalue()), save=False
            )
            figurita.estado = EstadoProceso.COMPLETADO
            figurita.fecha_generacion = timezone.now()
            figurita.nombre_mostrado = nombre
            figurita.datos_renderizados = datos_renderizados
            figurita.metadata = {"configuracion_aplicada": config}
            figurita.mensaje_error = ""
            figurita.save()

        ServicioSesiones.sincronizar_estado_proceso(sesion=figurita.sesion)
        logger.info("Figurita generada", extra={"figurita_id": figurita_id})
        return figurita


def _interpolar_color(color_inicio: str, color_fin: str, proporcion: float):
    def a_rgb(color: str):
        color = color.lstrip("#")
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))

    inicio = a_rgb(color_inicio)
    fin = a_rgb(color_fin)
    return tuple(int(inicio[i] + (fin[i] - inicio[i]) * proporcion) for i in range(3))
