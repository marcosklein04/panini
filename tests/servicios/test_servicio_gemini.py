import io
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from PIL import Image, ImageDraw

from imagenes.services.servicio_gemini import ServicioGemini


@override_settings(GEMINI_API_KEY="clave-prueba", GEMINI_MODEL="gemini-2.5-flash")
class ServicioGeminiTest(SimpleTestCase):
    @patch("imagenes.services.servicio_gemini.genai.Client")
    def test_normaliza_segmentos_desde_json(self, mock_client):
        cliente = MagicMock()
        cliente.models.generate_content.return_value.text = (
            '{"segmentos":[{"label":"persona","box_2d":[10,20,900,800],"mask":"abc"}]}'
        )
        mock_client.return_value = cliente

        servicio = ServicioGemini()
        resultado = servicio.analizar_persona(b"imagen", "image/png")

        self.assertEqual(resultado["modelo"], "gemini-2.5-flash")
        self.assertEqual(len(resultado["segmentos"]), 1)
        self.assertEqual(resultado["segmentos"][0]["label"], "persona")

    @override_settings(
        GEMINI_API_KEY="tu_api_key_de_gemini",
        GEMINI_MODEL="gemini-2.5-flash",
        GEMINI_MODO_SIMULADO=True,
    )
    def test_genera_segmento_local_en_modo_simulado(self):
        imagen = Image.new("RGB", (400, 600), "white")
        dibujo = ImageDraw.Draw(imagen)
        dibujo.ellipse((120, 50, 280, 210), fill="red")
        dibujo.rectangle((150, 180, 250, 520), fill="red")
        buffer = io.BytesIO()
        imagen.save(buffer, format="PNG")

        servicio = ServicioGemini()
        resultado = servicio.analizar_persona(buffer.getvalue(), "image/png")

        self.assertEqual(resultado["modelo"], "gemini-simulado-local")
        self.assertEqual(len(resultado["segmentos"]), 1)
        self.assertEqual(resultado["segmentos"][0]["label"], "persona")
