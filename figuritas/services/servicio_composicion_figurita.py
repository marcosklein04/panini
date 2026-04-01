from __future__ import annotations

import io
import logging
from pathlib import Path

import cv2
import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from core.enums import EstadoProceso
from core.excepciones import ErrorDeDominio
from figuritas.models import FiguritaGenerada, PlantillaFigurita
from sesiones.services.servicio_sesiones import ServicioSesiones
from trivias.services.servicio_validacion_sticker import ServicioValidacionSticker

logger = logging.getLogger(__name__)


class ServicioComposicionFigurita:
    CONFIG_DEFAULT = {
        "ancho": 768,
        "alto": 1152,
        "color_fondo_inicio": "#0F6CBD",
        "color_fondo_fin": "#7BE0FF",
        "color_marco": "#F7D35B",
        "color_texto": "#FFFFFF",
        "color_texto_secundario": "#FFEAA0",
        "titulo_superior": "EDICION PERSONALIZADA",
        "subtitulo": "STICKER FAN CARD",
        "badge": "TITULAR",
        "escala_persona": 0.9,
        "desplazamiento_x": 0,
        "desplazamiento_y": 10,
        "proporcion_busto": 0.9,
        "margen_horizontal_busto": 0.08,
        "margen_superior_busto": 0.05,
        "margen_inferior_busto": 0.08,
        "umbral_alpha_persona": 20,
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
            Path("C:/Windows/Fonts/bahnschrift.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf") if negrita else Path("C:/Windows/Fonts/arial.ttf"),
            "Arial.ttf",
            "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf",
        ]
        for nombre in candidatos:
            try:
                return ImageFont.truetype(nombre, tamano)
            except OSError:
                continue
        return ImageFont.load_default()

    @staticmethod
    def _ruta_plantilla_demo() -> Path | None:
        rutas = [
            settings.BASE_DIR / "figu-maker-ia-vanilla" / "assets" / "img" / "panini-img.png",
            settings.BASE_DIR / "figu-maker-ia-vanilla" / "assets" / "img" / "plantilla-figurita.png",
            settings.BASE_DIR / "core" / "static" / "core" / "panini-img.png",
            settings.BASE_DIR / "core" / "static" / "core" / "plantilla-figurita.png",
        ]
        for ruta in rutas:
            if ruta.exists():
                return ruta
        return None

    @staticmethod
    def _crear_fondo(
        configuracion: dict, plantilla: PlantillaFigurita
    ) -> tuple[Image.Image, bool]:
        ancho = configuracion["ancho"]
        alto = configuracion["alto"]
        ruta_demo = ServicioComposicionFigurita._ruta_plantilla_demo()
        if ruta_demo:
            fondo = Image.open(ruta_demo).convert("RGBA")
            return fondo.resize((ancho, alto)), True

        if plantilla.archivo_base:
            with plantilla.archivo_base.open("rb") as descriptor:
                fondo = Image.open(descriptor).convert("RGBA")
                return fondo.resize((ancho, alto)), True

        color_inicio = configuracion["color_fondo_inicio"]
        color_fin = configuracion["color_fondo_fin"]
        fondo = Image.new("RGBA", (ancho, alto), color_inicio)
        dibujo = ImageDraw.Draw(fondo)
        for y in range(alto):
            proporcion = y / max(alto - 1, 1)
            color = _interpolar_color(color_inicio, color_fin, proporcion)
            dibujo.line([(0, y), (ancho, y)], fill=color)
        return fondo, False

    @staticmethod
    def _limpiar_alpha_persona(persona: Image.Image, umbral: int) -> Image.Image:
        persona = persona.copy()
        alpha = persona.getchannel("A")
        alpha = alpha.point(lambda valor: 0 if valor < umbral else (255 if valor > 245 else valor))
        persona.putalpha(alpha)
        return persona

    @staticmethod
    def _recortar_a_busto(persona: Image.Image, config: dict) -> Image.Image:
        umbral = int(config.get("umbral_alpha_persona", 20))
        persona = ServicioComposicionFigurita._limpiar_alpha_persona(persona, umbral)
        alpha = persona.getchannel("A")
        caja = alpha.point(lambda valor: 255 if valor >= umbral else 0).getbbox()
        if not caja:
            return persona

        persona = persona.crop(caja)
        alpha = persona.getchannel("A")
        caja = alpha.point(lambda valor: 255 if valor >= umbral else 0).getbbox()
        if not caja:
            return persona

        x0, y0, x1, y1 = caja
        ancho = max(x1 - x0, 1)
        alto = max(y1 - y0, 1)
        limite_busto = y0 + int(alto * float(config.get("proporcion_busto", 0.68)))
        margen_x = int(ancho * float(config.get("margen_horizontal_busto", 0.14)))
        margen_superior = int(alto * float(config.get("margen_superior_busto", 0.05)))
        margen_inferior = int(alto * float(config.get("margen_inferior_busto", 0.05)))

        caja_busto = (
            max(x0 - margen_x, 0),
            max(y0 - margen_superior, 0),
            min(x1 + margen_x, persona.width),
            min(limite_busto + margen_inferior, persona.height),
        )
        persona = persona.crop(caja_busto)
        alpha = persona.getchannel("A")
        caja_final = alpha.point(lambda valor: 255 if valor >= umbral else 0).getbbox()
        if caja_final:
            persona = persona.crop(caja_final)
        return persona

    @staticmethod
    def _crear_mascara_silueta_plantilla(fondo: Image.Image) -> Image.Image:
        ancho, alto = fondo.size
        matriz = np.array(fondo.convert("RGB"))
        hsv = cv2.cvtColor(matriz, cv2.COLOR_RGB2HSV)
        mascara_blanco = cv2.inRange(hsv, (0, 0, 210), (180, 70, 255))
        num_etiquetas, etiquetas, estadisticas, _ = cv2.connectedComponentsWithStats(
            mascara_blanco
        )

        mejor_etiqueta = None
        mejor_puntaje = float("-inf")
        for etiqueta in range(1, num_etiquetas):
            x, y, w, h, area = estadisticas[etiqueta]
            if area < int(ancho * alto * 0.06):
                continue
            centro_x = x + (w / 2)
            centro_y = y + (h / 2)
            if centro_x > (ancho * 0.62):
                continue
            if centro_y < (alto * 0.12) or centro_y > (alto * 0.82):
                continue
            puntaje = (
                area
                - abs(centro_x - (ancho * 0.33)) * 220
                - abs(centro_y - (alto * 0.47)) * 120
            )
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_etiqueta = etiqueta

        if mejor_etiqueta is not None:
            mascara = np.zeros((alto, ancho), dtype=np.uint8)
            mascara[etiquetas == mejor_etiqueta] = 255
            mascara = cv2.morphologyEx(
                mascara,
                cv2.MORPH_CLOSE,
                np.ones((11, 11), np.uint8),
                iterations=2,
            )
            mascara = cv2.GaussianBlur(mascara, (0, 0), sigmaX=max(1, int(ancho / 280)))
            return Image.fromarray(mascara, mode="L")

        def sx(valor_x: int, valor_y: int) -> tuple[int, int]:
            return (
                int(valor_x * ancho / 1024),
                int(valor_y * alto / 1536),
            )

        mascara = Image.new("L", (ancho, alto), 0)
        dibujo = ImageDraw.Draw(mascara)

        cabeza = [sx(215, 240), sx(421, 520)]
        cuello = [sx(255, 430), sx(380, 690)]
        cuerpo = [sx(48, 650), sx(621, 1250)]
        hombro_derecho = [sx(445, 620), sx(686, 900)]
        hombro_izquierdo = [sx(-60, 720), sx(170, 980)]

        dibujo.ellipse(cabeza, fill=255)
        dibujo.rectangle(cuello, fill=255)
        dibujo.rounded_rectangle(cuerpo, radius=int(82 * ancho / 1024), fill=255)
        dibujo.ellipse(hombro_derecho, fill=255)
        dibujo.ellipse(hombro_izquierdo, fill=255)
        dibujo.polygon(
            [
                sx(0, 805),
                sx(140, 690),
                sx(258, 660),
                sx(48, 980),
            ],
            fill=255,
        )
        return mascara.filter(ImageFilter.GaussianBlur(radius=max(1, int(ancho / 384))))

    @staticmethod
    def _extraer_layout_plantilla_visual(fondo: Image.Image) -> dict:
        ancho, alto = fondo.size

        def escalar_caja(caja_base):
            x0, y0, x1, y1 = caja_base
            return (
                int(x0 * ancho / 768),
                int(y0 * alto / 1152),
                int(x1 * ancho / 768),
                int(y1 * alto / 1152),
            )

        layout_default = {
            "barra_nombre": escalar_caja((32, 930, 621, 1041)),
            "barra_equipo": escalar_caja((62, 1065, 541, 1116)),
            "zona_persona": escalar_caja((22, 58, 600, 910)),
            "centro_persona_x": int(ancho * 0.39),
            "base_persona_y": escalar_caja((0, 936, 0, 0))[1],
        }

        try:
            matriz = np.array(fondo.convert("RGB"))
            hsv = cv2.cvtColor(matriz, cv2.COLOR_RGB2HSV)

            mascara_barras = cv2.inRange(hsv, (70, 40, 40), (110, 255, 205))
            num_etiquetas, _, estadisticas, _ = cv2.connectedComponentsWithStats(mascara_barras)
            candidatos = []
            for etiqueta in range(1, num_etiquetas):
                x, y, w, h, area = estadisticas[etiqueta]
                if area < int((ancho * alto) * 0.008):
                    continue
                candidatos.append(
                    {
                        "bbox": (int(x), int(y), int(x + w), int(y + h)),
                        "area": int(area),
                        "ancho": int(w),
                        "alto": int(h),
                        "y": int(y),
                    }
                )

            barra_nombre = None
            barra_equipo = None
            if candidatos:
                barra_nombre = max(
                    candidatos,
                    key=lambda item: (
                        item["ancho"],
                        -abs(item["y"] - int(alto * 0.80)),
                    ),
                )["bbox"]
                resto = [item for item in candidatos if item["bbox"] != barra_nombre]
                if resto:
                    barra_equipo = max(
                        resto,
                        key=lambda item: (
                            item["ancho"],
                            -abs(item["y"] - int(alto * 0.91)),
                        ),
                    )["bbox"]

            if (
                barra_nombre
                and barra_equipo
                and (barra_nombre[3] - barra_nombre[1]) < int(alto * 0.16)
                and (barra_equipo[3] - barra_equipo[1]) < int(alto * 0.10)
            ):
                top_persona = int(alto * 0.06)
                centro_persona_x = int(ancho * 0.39)
                base_persona_y = barra_nombre[1] + int(alto * 0.01)
                zona_persona = (
                    int(ancho * 0.02),
                    top_persona,
                    int(ancho * 0.68),
                    barra_nombre[1] - int(alto * 0.035),
                )
                return {
                    "barra_nombre": barra_nombre,
                    "barra_equipo": barra_equipo,
                    "zona_persona": zona_persona,
                    "centro_persona_x": centro_persona_x,
                    "base_persona_y": base_persona_y,
                }
        except Exception:
            logger.warning("No se pudo extraer el layout de la plantilla; se usan valores por defecto.")

        return layout_default

    @staticmethod
    def _formatear_altura(altura_cm: int | None) -> str:
        if not altura_cm:
            return "--"
        metros = altura_cm / 100
        return f"{metros:.2f}".replace(".", ",") + "m"

    @staticmethod
    def _limpiar_textos_base_plantilla(fondo: Image.Image, cajas: list[tuple[int, int, int, int]]) -> Image.Image:
        fondo_limpio = fondo.copy()
        matriz = np.array(fondo_limpio.convert("RGBA"))

        for x0, y0, x1, y1 in cajas:
            if x1 <= x0 or y1 <= y0:
                continue
            region_rgba = matriz[y0:y1, x0:x1].copy()
            region_rgb = cv2.cvtColor(region_rgba, cv2.COLOR_RGBA2RGB)
            hsv = cv2.cvtColor(region_rgb, cv2.COLOR_RGB2HSV)

            mascara_blanco = cv2.inRange(hsv, (0, 0, 170), (180, 85, 255))
            mascara_amarillo = cv2.inRange(hsv, (12, 80, 120), (42, 255, 255))
            mascara_texto = cv2.bitwise_or(mascara_blanco, mascara_amarillo)
            mascara_texto = cv2.dilate(mascara_texto, np.ones((3, 3), np.uint8), iterations=1)

            if np.count_nonzero(mascara_texto) == 0:
                continue

            region_bgr = cv2.cvtColor(region_rgb, cv2.COLOR_RGB2BGR)
            region_limpia = cv2.inpaint(region_bgr, mascara_texto, 5, cv2.INPAINT_TELEA)
            region_limpia = cv2.cvtColor(region_limpia, cv2.COLOR_BGR2RGBA)
            region_limpia[:, :, 3] = region_rgba[:, :, 3]
            matriz[y0:y1, x0:x1] = region_limpia

        return Image.fromarray(matriz, mode="RGBA")

    @staticmethod
    def _dibujar_texto_con_sombra(
        dibujo: ImageDraw.ImageDraw,
        posicion: tuple[int, int],
        texto: str,
        *,
        fuente,
        color: str = "#FFFFFF",
        color_sombra: tuple[int, int, int, int] = (0, 0, 0, 115),
        desplazamiento: tuple[int, int] = (0, 3),
    ):
        x, y = posicion
        dx, dy = desplazamiento
        dibujo.text((x + dx, y + dy), texto, font=fuente, fill=color_sombra)
        dibujo.text((x, y), texto, font=fuente, fill=color)

    @staticmethod
    def _componer_sobre_plantilla_visual(*, fondo, persona, config, datos_sticker):
        ancho = config["ancho"]
        alto = config["alto"]
        layout = ServicioComposicionFigurita._extraer_layout_plantilla_visual(fondo)
        barra_nombre = layout["barra_nombre"]
        barra_equipo = layout["barra_equipo"]
        mascara_silueta = ServicioComposicionFigurita._crear_mascara_silueta_plantilla(
            fondo
        )
        caja_silueta = mascara_silueta.getbbox() or layout["zona_persona"]
        zona_persona = caja_silueta

        sombra = persona.copy()
        alfa_sombra = sombra.getchannel("A").filter(ImageFilter.GaussianBlur(radius=20))
        sombra.putalpha(alfa_sombra)

        escala = float(config.get("escala_persona", 0.9))
        max_alto_persona = int((zona_persona[3] - zona_persona[1]) * 1.08)
        max_ancho_persona = int((zona_persona[2] - zona_persona[0]) * 1.12)
        proporcion = min(
            max_alto_persona / max(persona.height, 1),
            max_ancho_persona / max(persona.width, 1),
        )
        nuevo_tamano = (int(persona.width * proporcion), int(persona.height * proporcion))
        persona = persona.resize(nuevo_tamano, Image.Resampling.LANCZOS)
        sombra = sombra.resize(nuevo_tamano, Image.Resampling.LANCZOS)

        centro_x = int((zona_persona[0] + zona_persona[2]) / 2) + int(
            config.get("desplazamiento_x", 0)
        )
        base_y = zona_persona[3] + int(config.get("desplazamiento_y", 0))
        posicion_persona = (centro_x - persona.width // 2, base_y - persona.height)
        posicion_sombra = (posicion_persona[0] + 14, posicion_persona[1] + 20)

        capa_sombra = Image.new("RGBA", fondo.size, (0, 0, 0, 0))
        capa_persona = Image.new("RGBA", fondo.size, (0, 0, 0, 0))
        capa_sombra.alpha_composite(sombra, posicion_sombra)
        capa_persona.alpha_composite(persona, posicion_persona)

        alpha_sombra = ImageChops.multiply(
            capa_sombra.getchannel("A"),
            mascara_silueta,
        )
        alpha_persona = ImageChops.multiply(
            capa_persona.getchannel("A"),
            mascara_silueta,
        )
        capa_sombra.putalpha(alpha_sombra)
        capa_persona.putalpha(alpha_persona)

        fondo.alpha_composite(capa_sombra)
        fondo.alpha_composite(capa_persona)

        dibujo = ImageDraw.Draw(fondo)
        fuente_nombre = ServicioComposicionFigurita._cargar_fuente(40, negrita=False)
        fuente_apellido = ServicioComposicionFigurita._cargar_fuente(40, negrita=True)
        fuente_info = ServicioComposicionFigurita._cargar_fuente(27, negrita=False)
        fuente_equipo = ServicioComposicionFigurita._cargar_fuente(31, negrita=True)
        fuente_pais = ServicioComposicionFigurita._cargar_fuente(26, negrita=False)

        nombre_x = barra_nombre[0] + 34
        nombre_y = barra_nombre[1] + 10
        nombre_jugador = (datos_sticker.nombre or "Jugador").upper()
        apellido_jugador = (datos_sticker.apellido or "Premium").upper()
        ServicioComposicionFigurita._dibujar_texto_con_sombra(
            dibujo,
            (nombre_x, nombre_y),
            nombre_jugador,
            fuente=fuente_nombre,
        )
        caja_nombre = dibujo.textbbox(
            (nombre_x, nombre_y),
            nombre_jugador,
            font=fuente_nombre,
        )
        apellido_x = caja_nombre[2] + 14
        ServicioComposicionFigurita._dibujar_texto_con_sombra(
            dibujo,
            (apellido_x, nombre_y),
            apellido_jugador,
            fuente=fuente_apellido,
        )

        linea_secundaria = " | ".join(
            [
                datos_sticker.fecha_nacimiento.strftime("%d-%m-%Y"),
                ServicioComposicionFigurita._formatear_altura(datos_sticker.altura_cm),
                f"{datos_sticker.peso_kg} kg",
            ]
        )
        ServicioComposicionFigurita._dibujar_texto_con_sombra(
            dibujo,
            (nombre_x, barra_nombre[1] + 60),
            linea_secundaria,
            fuente=fuente_info,
        )
        ServicioComposicionFigurita._dibujar_texto_con_sombra(
            dibujo,
            (barra_equipo[0] + 24, barra_equipo[1] + 6),
            (datos_sticker.equipo or "Equipo").upper(),
            fuente=fuente_equipo,
        )
        pais = f"({(datos_sticker.nacionalidad or 'ARG').upper()})"
        caja_pais = dibujo.textbbox((0, 0), pais, font=fuente_pais)
        pais_x = barra_equipo[2] - (caja_pais[2] - caja_pais[0]) - 24
        ServicioComposicionFigurita._dibujar_texto_con_sombra(
            dibujo,
            (pais_x, barra_equipo[1] + 8),
            pais,
            fuente=fuente_pais,
        )

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
        fondo, usa_plantilla_visual = ServicioComposicionFigurita._crear_fondo(
            config, figurita.plantilla
        )
        ancho = config["ancho"]
        alto = config["alto"]

        with figurita.resultado_recorte.png_transparente.open("rb") as descriptor:
            persona = Image.open(descriptor).convert("RGBA")
        persona = ServicioComposicionFigurita._recortar_a_busto(persona, config)

        nombre = ServicioComposicionFigurita._nombre_mostrado(datos_sticker).upper()
        if usa_plantilla_visual:
            fondo = ServicioComposicionFigurita._componer_sobre_plantilla_visual(
                fondo=fondo,
                persona=persona,
                config=config,
                datos_sticker=datos_sticker,
            )
        else:
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
            base_y = 980 + int(config["desplazamiento_y"])
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


def _dibujar_rectangulo_redondeado_con_gradiente(
    imagen: Image.Image,
    caja: tuple[int, int, int, int],
    *,
    radio: int,
    color_inicio: str,
    color_fin: str,
):
    x0, y0, x1, y1 = caja
    ancho = max(x1 - x0, 1)
    alto = max(y1 - y0, 1)
    gradiente = Image.new("RGBA", (ancho, alto))
    gradiente_dibujo = ImageDraw.Draw(gradiente)
    for y in range(alto):
        proporcion = y / max(alto - 1, 1)
        color = _interpolar_color(color_inicio, color_fin, proporcion)
        gradiente_dibujo.line([(0, y), (ancho, y)], fill=color)

    mascara = Image.new("L", (ancho, alto), 0)
    mascara_dibujo = ImageDraw.Draw(mascara)
    mascara_dibujo.rounded_rectangle([(0, 0), (ancho, alto)], radius=radio, fill=255)
    imagen.paste(gradiente, (x0, y0), mascara)
