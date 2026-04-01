from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from tests.factories.datos import (
    crear_archivo_imagen,
    crear_plantilla_demo,
    crear_respuesta_gemini_prueba,
    crear_trivia_demo,
)

MEDIA_ROOT_TEST = Path(__file__).resolve().parents[2] / ".test_media" / "api_flujo"
MEDIA_ROOT_TEST.mkdir(parents=True, exist_ok=True)
STORAGES_TEST = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(MEDIA_ROOT_TEST), "base_url": "/media/"},
    },
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(
    MEDIA_ROOT=MEDIA_ROOT_TEST,
    STORAGES=STORAGES_TEST,
    GEMINI_API_KEY="clave",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class FlujoCriticoApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.trivia, self.preguntas, self.equipo = crear_trivia_demo()
        crear_plantilla_demo()

    @patch(
        "imagenes.services.servicio_recorte_imagen.ServicioGemini.analizar_persona",
        return_value=crear_respuesta_gemini_prueba(),
    )
    def test_flujo_completo_anonimo_hasta_figurita(self, mock_gemini):
        respuesta_inicio = self.client.post("/api/sesiones/iniciar/", {}, format="json")
        self.assertEqual(respuesta_inicio.status_code, 201)
        token_publico = respuesta_inicio.json()["sesion"]["token_publico"]

        respuesta_trivia = self.client.get("/api/trivias/activa/")
        self.assertEqual(respuesta_trivia.status_code, 200)
        self.assertEqual(respuesta_trivia.json()["nombre"], "Ficha del jugador")

        respuesta_equipos = self.client.get("/api/catalogos/equipos/?q=river")
        self.assertEqual(respuesta_equipos.status_code, 200)
        self.assertGreaterEqual(len(respuesta_equipos.json()), 1)

        respuesta_preguntas = self.client.get(f"/api/sesiones/{token_publico}/preguntas/")
        self.assertEqual(respuesta_preguntas.status_code, 200)
        self.assertEqual(len(respuesta_preguntas.json()["preguntas"]), 6)

        payload_respuestas = {
            "respuestas": [
                {"pregunta_id": str(self.preguntas["nombre"].id), "valor": "Lionel"},
                {"pregunta_id": str(self.preguntas["apellido"].id), "valor": "Messi"},
                {
                    "pregunta_id": str(self.preguntas["fecha_nacimiento"].id),
                    "valor": "1987-06-24",
                },
                {"pregunta_id": str(self.preguntas["altura_cm"].id), "valor": 170},
                {"pregunta_id": str(self.preguntas["peso_kg"].id), "valor": 72},
                {
                    "pregunta_id": str(self.preguntas["equipo"].id),
                    "equipo_id": str(self.equipo.id),
                },
            ]
        }
        respuesta_responder = self.client.post(
            f"/api/sesiones/{token_publico}/responder/",
            payload_respuestas,
            format="json",
        )
        self.assertEqual(respuesta_responder.status_code, 200)
        self.assertTrue(respuesta_responder.json()["sesion"]["puede_subir_foto"])

        respuesta_estado = self.client.get(f"/api/sesiones/{token_publico}/estado/")
        self.assertEqual(respuesta_estado.status_code, 200)
        self.assertEqual(respuesta_estado.json()["datos_sticker"]["nombre"], "Lionel")
        self.assertEqual(respuesta_estado.json()["datos_sticker"]["equipo"], self.equipo.nombre)

        archivo = crear_archivo_imagen()
        respuesta_subida = self.client.post(
            f"/api/sesiones/{token_publico}/imagenes/subir/",
            {"archivo": archivo},
        )
        self.assertEqual(respuesta_subida.status_code, 201)
        foto_id = respuesta_subida.json()["foto"]["id"]

        respuesta_procesar = self.client.post(
            f"/api/imagenes/{foto_id}/procesar/",
            {"token_publico": token_publico},
            format="json",
        )
        self.assertEqual(respuesta_procesar.status_code, 202)
        self.assertEqual(respuesta_procesar.json()["resultado"]["estado"], "completado")
        resultado_id = respuesta_procesar.json()["resultado"]["id"]

        respuesta_resultado = self.client.get(f"/api/imagenes/{foto_id}/resultado/")
        self.assertEqual(respuesta_resultado.status_code, 200)
        self.assertEqual(respuesta_resultado.json()["estado"], "completado")
        self.assertIsNotNone(respuesta_resultado.json()["png_transparente_url"])

        respuesta_generar = self.client.post(
            f"/api/sesiones/{token_publico}/figuritas/generar/",
            {"resultado_recorte_id": resultado_id},
            format="json",
        )
        self.assertEqual(respuesta_generar.status_code, 202)
        figurita_id = respuesta_generar.json()["figurita"]["id"]

        respuesta_figurita = self.client.get(f"/api/figuritas/{figurita_id}/")
        self.assertEqual(respuesta_figurita.status_code, 200)
        self.assertEqual(respuesta_figurita.json()["estado"], "completado")
        self.assertEqual(respuesta_figurita.json()["datos_renderizados"]["nombre"], "Lionel")
        self.assertEqual(
            respuesta_figurita.json()["datos_renderizados"]["equipo"], self.equipo.nombre
        )
        self.assertIsNotNone(respuesta_figurita.json()["imagen_final_url"])

    def test_no_permite_subir_foto_antes_de_completar_preguntas(self):
        respuesta_inicio = self.client.post("/api/sesiones/iniciar/", {}, format="json")
        token_publico = respuesta_inicio.json()["sesion"]["token_publico"]

        respuesta_subida = self.client.post(
            f"/api/sesiones/{token_publico}/imagenes/subir/",
            {"archivo": crear_archivo_imagen()},
        )

        self.assertEqual(respuesta_subida.status_code, 409)
        self.assertEqual(respuesta_subida.json()["error"]["codigo"], "trivia_incompleta")

    def test_rechaza_altura_invalida_por_api(self):
        respuesta_inicio = self.client.post("/api/sesiones/iniciar/", {}, format="json")
        token_publico = respuesta_inicio.json()["sesion"]["token_publico"]

        respuesta = self.client.post(
            f"/api/sesiones/{token_publico}/responder/",
            {
                "pregunta_id": str(self.preguntas["altura_cm"].id),
                "valor": 20,
            },
            format="json",
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"]["codigo"], "numero_fuera_de_rango")
