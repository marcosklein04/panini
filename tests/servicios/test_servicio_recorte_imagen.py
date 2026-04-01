from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from PIL import Image

from core.excepciones import ErrorDeDominio
from imagenes.services.servicio_recorte_imagen import ServicioRecorteImagen
from tests.factories.datos import (
    crear_archivo_imagen,
    crear_plantilla_demo,
    crear_payload_respuestas_validas,
    crear_respuesta_gemini_prueba,
    crear_sesion_demo,
    crear_trivia_demo,
)
from trivias.services.servicio_trivia import ServicioTrivia

MEDIA_ROOT_TEST = Path(__file__).resolve().parents[2] / ".test_media" / "servicios_recorte"
MEDIA_ROOT_TEST.mkdir(parents=True, exist_ok=True)
STORAGES_TEST = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(MEDIA_ROOT_TEST), "base_url": "/media/"},
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(MEDIA_ROOT=MEDIA_ROOT_TEST, STORAGES=STORAGES_TEST, GEMINI_API_KEY="clave")
class ServicioRecorteImagenTest(TestCase):
    def setUp(self):
        self.trivia, self.preguntas, self.equipo = crear_trivia_demo()
        crear_plantilla_demo()
        self.sesion = crear_sesion_demo(trivia=self.trivia)
        ServicioTrivia.responder_sesion(
            sesion=self.sesion,
            payload={
                "respuestas": crear_payload_respuestas_validas(
                    preguntas=self.preguntas,
                    equipo=self.equipo,
                )
            },
        )

    @patch(
        "imagenes.services.servicio_recorte_imagen.ServicioGemini.analizar_persona",
        return_value=crear_respuesta_gemini_prueba(),
    )
    def test_guardar_y_procesar_foto_genera_recorte(self, mock_gemini):
        archivo = crear_archivo_imagen()
        foto = ServicioRecorteImagen.guardar_foto_original(
            sesion=self.sesion,
            archivo=archivo,
        )
        resultado, ya_existente = ServicioRecorteImagen.preparar_procesamiento(foto=foto)

        self.assertFalse(ya_existente)
        resultado = ServicioRecorteImagen.procesar_foto(foto_id=foto.id)

        self.assertEqual(resultado.estado, "completado")
        self.assertTrue(resultado.png_transparente.name.endswith(".png"))
        self.assertTrue(resultado.archivo_mascara.name.endswith(".png"))
        self.assertEqual(
            resultado.metadatos_recorte["segmento_seleccionado"]["label"], "persona"
        )

        with resultado.png_transparente.open("rb") as descriptor:
            imagen = Image.open(descriptor)
            self.assertEqual(imagen.mode, "RGBA")

    def test_no_permite_procesamiento_duplicado(self):
        archivo = crear_archivo_imagen(nombre="foto-2.png")
        foto = ServicioRecorteImagen.guardar_foto_original(
            sesion=self.sesion,
            archivo=archivo,
        )
        ServicioRecorteImagen.preparar_procesamiento(foto=foto)

        with self.assertRaisesMessage(
            ErrorDeDominio, "Esta foto ya tiene un procesamiento activo."
        ):
            ServicioRecorteImagen.preparar_procesamiento(foto=foto)
