from pathlib import Path

from django.core.files.base import File
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from catalogos.models import Equipo
from figuritas.models import PlantillaFigurita
from trivias.models import PreguntaTrivia, Trivia


class Command(BaseCommand):
    help = "Carga un flujo de preguntas demo, equipos y una plantilla predeterminada."

    @transaction.atomic
    def handle(self, *args, **options):
        Trivia.objects.update(activa=False)
        trivia, _ = Trivia.objects.update_or_create(
            nombre="Ficha del jugador",
            defaults={
                "descripcion": "Cuestionario inicial para completar la figurita personalizada.",
                "activa": True,
            },
        )

        equipos = [
            ("River Plate", "Argentina"),
            ("Boca Juniors", "Argentina"),
            ("San Lorenzo", "Argentina"),
            ("Racing Club", "Argentina"),
            ("Independiente", "Argentina"),
        ]
        for orden, (nombre, pais) in enumerate(equipos, start=1):
            Equipo.objects.update_or_create(
                nombre=nombre,
                defaults={"pais": pais, "orden": orden, "activa": True},
            )

        preguntas = [
            {
                "codigo": "nombre",
                "texto": "¿Como te llamas?",
                "tipo_respuesta": "texto",
                "orden": 1,
                "placeholder": "Ingresa tu nombre",
                "mapea_a_campo_sticker": "nombre",
            },
            {
                "codigo": "apellido",
                "texto": "¿Cual es tu apellido?",
                "tipo_respuesta": "texto",
                "orden": 2,
                "placeholder": "Ingresa tu apellido",
                "mapea_a_campo_sticker": "apellido",
            },
            {
                "codigo": "fecha_nacimiento",
                "texto": "¿Cual es tu fecha de nacimiento?",
                "tipo_respuesta": "fecha",
                "orden": 3,
                "placeholder": "YYYY-MM-DD",
                "mapea_a_campo_sticker": "fecha_nacimiento",
            },
            {
                "codigo": "altura_cm",
                "texto": "¿Cuanto mides en centimetros?",
                "tipo_respuesta": "numero",
                "orden": 4,
                "placeholder": "180",
                "mapea_a_campo_sticker": "altura_cm",
            },
            {
                "codigo": "peso_kg",
                "texto": "¿Cuanto pesas en kilos?",
                "tipo_respuesta": "numero",
                "orden": 5,
                "placeholder": "75",
                "mapea_a_campo_sticker": "peso_kg",
            },
            {
                "codigo": "equipo",
                "texto": "¿Para que equipo juegas?",
                "tipo_respuesta": "select_busqueda",
                "orden": 6,
                "placeholder": "Busca tu equipo",
                "mapea_a_campo_sticker": "equipo",
            },
            {
                "codigo": "apodo",
                "texto": "¿Tienes apodo?",
                "tipo_respuesta": "texto",
                "orden": 7,
                "placeholder": "Opcional",
                "mapea_a_campo_sticker": "apodo",
            },
        ]

        for item in preguntas:
            PreguntaTrivia.objects.update_or_create(
                trivia=trivia,
                codigo=item["codigo"],
                defaults={
                    "texto": item["texto"],
                    "tipo_respuesta": item["tipo_respuesta"],
                    "orden": item["orden"],
                    "obligatoria": item["codigo"] != "apodo",
                    "placeholder": item["placeholder"],
                    "ayuda": "",
                    "activa": True,
                    "mapea_a_campo_sticker": item["mapea_a_campo_sticker"],
                    "reglas_validacion": {},
                },
            )

        PlantillaFigurita.objects.filter(predeterminada=True).update(predeterminada=False)
        plantilla, _ = PlantillaFigurita.objects.update_or_create(
            slug="clasica-azul",
            defaults={
                "nombre": "Clasica Azul",
                "activa": True,
                "predeterminada": True,
                "configuracion_visual": {
                    "ancho": 768,
                    "alto": 1152,
                    "color_fondo_inicio": "#0A4F8A",
                    "color_fondo_fin": "#4FC3FF",
                    "color_marco": "#F8D66D",
                    "color_texto": "#FFFFFF",
                    "color_texto_secundario": "#FFEAA0",
                    "titulo_superior": "FICHA COMPLETADA",
                    "subtitulo": "FIGURITA FAN EDITION",
                    "badge": "TOP",
                    "escala_persona": 0.88,
                    "desplazamiento_x": 0,
                    "desplazamiento_y": 10,
                    "proporcion_busto": 0.9,
                },
            },
        )

        ruta_asset = (
            Path(settings.BASE_DIR)
            / "figu-maker-ia-vanilla"
            / "assets"
            / "img"
            / "panini-img.png"
        )
        if ruta_asset.exists():
            with ruta_asset.open("rb") as descriptor:
                plantilla.archivo_base.save(
                    "clasica-azul-panini.png",
                    File(descriptor),
                    save=True,
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Datos demo listos. Trivia: {trivia.id} | Plantilla: {plantilla.id}"
            )
        )
