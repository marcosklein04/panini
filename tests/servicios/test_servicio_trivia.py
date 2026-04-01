from django.test import TestCase

from core.excepciones import ErrorDeDominio
from tests.factories.datos import (
    crear_payload_respuestas_validas,
    crear_sesion_demo,
    crear_trivia_demo,
)
from trivias.services.servicio_trivia import ServicioTrivia


class ServicioTriviaTest(TestCase):
    def setUp(self):
        self.trivia, self.preguntas, self.equipo = crear_trivia_demo()
        self.sesion = crear_sesion_demo(trivia=self.trivia)

    def test_responder_preguntas_validas_habilita_carga_foto(self):
        payload = {"respuestas": crear_payload_respuestas_validas(
            preguntas=self.preguntas,
            equipo=self.equipo,
        )}

        sesion, datos_sticker, respuestas_guardadas, evaluacion = ServicioTrivia.responder_sesion(
            sesion=self.sesion,
            payload=payload,
        )

        self.assertEqual(len(respuestas_guardadas), 6)
        self.assertTrue(evaluacion["es_completa"])
        self.assertTrue(sesion.trivia_completada)
        self.assertTrue(sesion.puede_subir_foto)
        self.assertEqual(datos_sticker.nombre, "Lionel")
        self.assertEqual(datos_sticker.apellido, "Messi")
        self.assertEqual(datos_sticker.equipo, self.equipo.nombre)

    def test_no_habilita_carga_si_faltan_campos_requeridos(self):
        payload = {
            "pregunta_id": self.preguntas["nombre"].id,
            "valor": "Lionel",
        }

        sesion, datos_sticker, respuestas_guardadas, evaluacion = ServicioTrivia.responder_sesion(
            sesion=self.sesion,
            payload=payload,
        )

        self.assertEqual(len(respuestas_guardadas), 1)
        self.assertFalse(evaluacion["es_completa"])
        self.assertFalse(sesion.trivia_completada)
        self.assertFalse(sesion.puede_subir_foto)
        self.assertIn("apellido", evaluacion["campos_faltantes"])

    def test_rechaza_altura_fuera_de_rango(self):
        with self.assertRaises(ErrorDeDominio) as contexto:
            ServicioTrivia.responder_sesion(
                sesion=self.sesion,
                payload={
                    "pregunta_id": self.preguntas["altura_cm"].id,
                    "valor": 40,
                },
            )

        self.assertEqual(contexto.exception.codigo, "numero_fuera_de_rango")

    def test_rechaza_fecha_fuera_de_rango(self):
        with self.assertRaises(ErrorDeDominio) as contexto:
            ServicioTrivia.responder_sesion(
                sesion=self.sesion,
                payload={
                    "pregunta_id": self.preguntas["fecha_nacimiento"].id,
                    "valor": "2024-01-01",
                },
            )

        self.assertEqual(contexto.exception.codigo, "edad_fuera_de_rango")
