from __future__ import annotations

import base64
import io
import json
import logging

import cv2
import numpy as np
from django.conf import settings
from google import genai
from google.genai import types
from PIL import Image

from core.excepciones import ErrorDeDominio

logger = logging.getLogger(__name__)


class ServicioGemini:
    def __init__(self) -> None:
        self.modelo = settings.GEMINI_MODEL
        self.modo_simulado = bool(getattr(settings, "GEMINI_MODO_SIMULADO", False))
        clave_invalida = settings.GEMINI_API_KEY.strip() in {"", "tu_api_key_de_gemini"}

        if self.modo_simulado and clave_invalida:
            logger.warning("ServicioGemini en modo simulado local.")
            self.cliente = None
            return

        if not settings.GEMINI_API_KEY:
            raise ErrorDeDominio(
                "La integracion con Gemini no esta configurada.",
                codigo="gemini_no_configurado",
                estado_http=503,
            )
        self.cliente = genai.Client(api_key=settings.GEMINI_API_KEY)

    def analizar_persona(self, imagen_bytes: bytes, mime_type: str) -> dict:
        if self.modo_simulado and self.cliente is None:
            return self._analizar_persona_simulada(imagen_bytes)

        prompt = (
            "Analiza esta imagen y detecta unicamente personas visibles. "
            "Responde solo JSON con la forma "
            '{"segmentos":[{"label":"persona","box_2d":[y0,x0,y1,x1],"mask":"<png_base64>"}]}. '
            "Usa coordenadas normalizadas entre 0 y 1000. "
            "Incluye solo segmentos de persona y omite cualquier texto adicional."
        )
        config = types.GenerateContentConfig(
            responseMimeType="application/json",
            thinkingConfig=types.ThinkingConfig(thinkingBudget=0),
        )
        respuesta = self.cliente.models.generate_content(
            model=self.modelo,
            contents=[types.Part.from_bytes(data=imagen_bytes, mime_type=mime_type), prompt],
            config=config,
        )
        texto = (respuesta.text or "").strip()
        if not texto:
            raise ErrorDeDominio(
                "Gemini no devolvio contenido para segmentar la imagen.",
                codigo="respuesta_gemini_vacia",
                estado_http=502,
            )

        try:
            bruto = json.loads(texto)
        except json.JSONDecodeError as exc:
            logger.exception("No se pudo interpretar la respuesta JSON de Gemini.")
            raise ErrorDeDominio(
                "Gemini devolvio una respuesta invalida para la segmentacion.",
                codigo="respuesta_gemini_invalida",
                estado_http=502,
            ) from exc

        segmentos = bruto.get("segmentos") if isinstance(bruto, dict) else bruto
        if not isinstance(segmentos, list):
            raise ErrorDeDominio(
                "Gemini no devolvio una lista de segmentos valida.",
                codigo="segmentos_invalidos",
                estado_http=502,
            )

        segmentos_normalizados = []
        for segmento in segmentos:
            if not isinstance(segmento, dict):
                continue
            label = str(segmento.get("label", "")).strip().lower()
            box_2d = segmento.get("box_2d")
            mask = segmento.get("mask")
            if not label or not isinstance(box_2d, list) or len(box_2d) != 4 or not mask:
                continue
            segmentos_normalizados.append(
                {"label": label, "box_2d": box_2d, "mask": mask}
            )

        if not segmentos_normalizados:
            raise ErrorDeDominio(
                "Gemini no encontro segmentos utilizables en la imagen.",
                codigo="segmentacion_sin_resultados",
                estado_http=422,
            )

        return {
            "modelo": self.modelo,
            "segmentos": segmentos_normalizados,
            "respuesta_cruda": bruto,
        }

    def _analizar_persona_simulada(self, imagen_bytes: bytes) -> dict:
        imagen = Image.open(io.BytesIO(imagen_bytes)).convert("RGB")
        ancho, alto = imagen.size
        imagen_np = cv2.cvtColor(np.array(imagen), cv2.COLOR_RGB2BGR)
        mascara = self._generar_mascara_local(imagen_np)

        indices = np.argwhere(mascara > 10)
        if indices.size == 0:
            x0 = int(ancho * 0.2)
            x1 = int(ancho * 0.8)
            y0 = int(alto * 0.08)
            y1 = int(alto * 0.92)
            mascara = np.zeros((alto, ancho), dtype=np.uint8)
            mascara[y0:y1, x0:x1] = 255
        else:
            y0, x0 = indices.min(axis=0)
            y1, x1 = indices.max(axis=0)

        caja_normalizada = [
            int((y0 / max(alto, 1)) * 1000),
            int((x0 / max(ancho, 1)) * 1000),
            int((y1 / max(alto, 1)) * 1000),
            int((x1 / max(ancho, 1)) * 1000),
        ]
        mascara_recorte = mascara[y0:y1 or alto, x0:x1 or ancho]
        if mascara_recorte.size == 0:
            mascara_recorte = mascara

        imagen_mascara = Image.fromarray(mascara_recorte, mode="L")
        buffer = io.BytesIO()
        imagen_mascara.save(buffer, format="PNG")
        mask_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        respuesta = {
            "segmentos": [
                {
                    "label": "persona",
                    "box_2d": caja_normalizada,
                    "mask": mask_b64,
                }
            ]
        }
        return {
            "modelo": "gemini-simulado-local",
            "segmentos": respuesta["segmentos"],
            "respuesta_cruda": respuesta,
        }

    def _generar_mascara_local(self, imagen_np: np.ndarray) -> np.ndarray:
        alto, ancho = imagen_np.shape[:2]
        mascara_grabcut = np.zeros((alto, ancho), np.uint8)
        fondo = np.zeros((1, 65), np.float64)
        primer_plano = np.zeros((1, 65), np.float64)
        rectangulo = (
            int(ancho * 0.1),
            int(alto * 0.05),
            int(ancho * 0.8),
            int(alto * 0.9),
        )
        try:
            cv2.grabCut(
                imagen_np,
                mascara_grabcut,
                rectangulo,
                fondo,
                primer_plano,
                4,
                cv2.GC_INIT_WITH_RECT,
            )
            mascara = np.where(
                (mascara_grabcut == cv2.GC_FGD) | (mascara_grabcut == cv2.GC_PR_FGD),
                255,
                0,
            ).astype(np.uint8)
        except cv2.error:
            mascara = np.zeros((alto, ancho), dtype=np.uint8)
            mascara[
                int(alto * 0.08) : int(alto * 0.92),
                int(ancho * 0.2) : int(ancho * 0.8),
            ] = 255
        return mascara
