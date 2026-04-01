from __future__ import annotations

import base64
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageDraw

from catalogos.models import Equipo
from figuritas.models import PlantillaFigurita
from sesiones.models import SesionProceso
from trivias.models import PreguntaTrivia, Trivia


def crear_equipos_demo() -> list[Equipo]:
    nombres = [
        ("River Plate", "Argentina"),
        ("Boca Juniors", "Argentina"),
        ("San Lorenzo", "Argentina"),
        ("Racing Club", "Argentina"),
    ]
    equipos = []
    for orden, (nombre, pais) in enumerate(nombres, start=1):
        equipo, _ = Equipo.objects.get_or_create(
            nombre=nombre,
            defaults={"pais": pais, "orden": orden, "activa": True},
        )
        equipos.append(equipo)
    return equipos


def crear_trivia_demo() -> tuple[Trivia, dict[str, PreguntaTrivia], Equipo]:
    Trivia.objects.update(activa=False)
    trivia = Trivia.objects.create(
        nombre="Ficha del jugador",
        descripcion="Cuestionario guiado para completar los datos de la figurita.",
        activa=True,
    )
    equipo = crear_equipos_demo()[0]
    configuracion = [
        {
            "codigo": "nombre",
            "texto": "¿Como te llamas?",
            "tipo_respuesta": "texto",
            "placeholder": "Ingresa tu nombre",
            "mapea_a_campo_sticker": "nombre",
        },
        {
            "codigo": "apellido",
            "texto": "¿Cual es tu apellido?",
            "tipo_respuesta": "texto",
            "placeholder": "Ingresa tu apellido",
            "mapea_a_campo_sticker": "apellido",
        },
        {
            "codigo": "fecha_nacimiento",
            "texto": "¿Cual es tu fecha de nacimiento?",
            "tipo_respuesta": "fecha",
            "placeholder": "YYYY-MM-DD",
            "mapea_a_campo_sticker": "fecha_nacimiento",
        },
        {
            "codigo": "altura_cm",
            "texto": "¿Cuanto mides en centimetros?",
            "tipo_respuesta": "numero",
            "placeholder": "180",
            "mapea_a_campo_sticker": "altura_cm",
        },
        {
            "codigo": "peso_kg",
            "texto": "¿Cuanto pesas en kilos?",
            "tipo_respuesta": "numero",
            "placeholder": "75",
            "mapea_a_campo_sticker": "peso_kg",
        },
        {
            "codigo": "equipo",
            "texto": "¿Para que equipo juegas?",
            "tipo_respuesta": "select_busqueda",
            "placeholder": "Busca tu equipo",
            "mapea_a_campo_sticker": "equipo",
        },
    ]
    preguntas = {}
    for orden, item in enumerate(configuracion, start=1):
        preguntas[item["codigo"]] = PreguntaTrivia.objects.create(
            trivia=trivia,
            codigo=item["codigo"],
            texto=item["texto"],
            tipo_respuesta=item["tipo_respuesta"],
            orden=orden,
            obligatoria=True,
            placeholder=item["placeholder"],
            ayuda="",
            activa=True,
            mapea_a_campo_sticker=item["mapea_a_campo_sticker"],
        )
    return trivia, preguntas, equipo


def crear_sesion_demo(*, trivia: Trivia | None = None) -> SesionProceso:
    if trivia is None:
        trivia, _, _ = crear_trivia_demo()
    return SesionProceso.objects.create(trivia=trivia)


def crear_payload_respuestas_validas(*, preguntas: dict[str, PreguntaTrivia], equipo: Equipo):
    return [
        {"pregunta_id": preguntas["nombre"].id, "valor": "Lionel"},
        {"pregunta_id": preguntas["apellido"].id, "valor": "Messi"},
        {"pregunta_id": preguntas["fecha_nacimiento"].id, "valor": "1987-06-24"},
        {"pregunta_id": preguntas["altura_cm"].id, "valor": 170},
        {"pregunta_id": preguntas["peso_kg"].id, "valor": 72},
        {"pregunta_id": preguntas["equipo"].id, "equipo_id": equipo.id},
    ]


def crear_plantilla_demo(**kwargs) -> PlantillaFigurita:
    datos = {
        "nombre": "Clasica Azul",
        "slug": "clasica-azul",
        "activa": True,
        "predeterminada": True,
        "configuracion_visual": {
            "ancho": 900,
            "alto": 1200,
            "color_fondo_inicio": "#0A4F8A",
            "color_fondo_fin": "#4FC3FF",
            "color_marco": "#F8D66D",
            "color_texto": "#FFFFFF",
            "color_texto_secundario": "#FFEAA0",
            "titulo_superior": "FICHA COMPLETADA",
            "subtitulo": "FIGURITA FAN EDITION",
            "badge": "TOP",
            "escala_persona": 0.9,
            "desplazamiento_x": 0,
            "desplazamiento_y": 10,
            "proporcion_busto": 0.9,
        },
    }
    datos.update(kwargs)
    PlantillaFigurita.objects.filter(predeterminada=True).update(predeterminada=False)
    return PlantillaFigurita.objects.create(**datos)


def crear_archivo_imagen(
    *,
    nombre: str = "foto.png",
    ancho: int = 800,
    alto: int = 1000,
    color=(200, 60, 60, 255),
):
    imagen = Image.new("RGBA", (ancho, alto), (245, 245, 245, 255))
    dibujo = ImageDraw.Draw(imagen)
    dibujo.ellipse((200, 90, 600, 450), fill=color)
    dibujo.rectangle((280, 420, 520, 900), fill=color)
    dibujo.rectangle((200, 450, 280, 800), fill=color)
    dibujo.rectangle((520, 450, 600, 800), fill=color)
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return SimpleUploadedFile(nombre, buffer.getvalue(), content_type="image/png")


def crear_respuesta_gemini_prueba() -> dict:
    mascara = Image.new("L", (240, 480), 0)
    dibujo = ImageDraw.Draw(mascara)
    dibujo.ellipse((25, 0, 215, 170), fill=255)
    dibujo.rectangle((70, 140, 170, 470), fill=255)
    dibujo.rectangle((30, 170, 75, 420), fill=255)
    dibujo.rectangle((165, 170, 210, 420), fill=255)
    buffer = io.BytesIO()
    mascara.save(buffer, format="PNG")
    mask_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return {
        "modelo": "gemini-2.5-flash",
        "segmentos": [
            {
                "label": "persona",
                "box_2d": [80, 200, 920, 800],
                "mask": mask_b64,
            }
        ],
        "respuesta_cruda": {
            "segmentos": [{"label": "persona", "box_2d": [80, 200, 920, 800]}]
        },
    }
