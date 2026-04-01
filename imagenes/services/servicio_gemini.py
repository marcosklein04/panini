from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor, TimeoutError as TiempoExcedidoFuture
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
        self.permite_fallback_local = bool(
            getattr(settings, "GEMINI_FALLBACK_LOCAL", False)
        )
        self.timeout_segundos = int(getattr(settings, "GEMINI_TIMEOUT_SEGUNDOS", 20))
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
            "Analiza esta imagen y detecta unicamente la persona principal visible. "
            "Responde solo JSON con la forma "
            '{"segmentos":[{"label":"persona","box_2d":[y0,x0,y1,x1],"mask":"<png_base64>"}]}. '
            "Usa coordenadas normalizadas entre 0 y 1000. "
            "La mascara debe incluir cabeza, cuello, hombros y torso superior, y excluir por completo fondo y objetos. "
            "Incluye solo segmentos de persona y omite cualquier texto adicional."
        )
        config = types.GenerateContentConfig(
            responseMimeType="application/json",
            thinkingConfig=types.ThinkingConfig(thinkingBudget=0),
        )
        try:
            respuesta = self._generar_con_timeout(
                imagen_bytes=imagen_bytes,
                mime_type=mime_type,
                prompt=prompt,
                config=config,
            )
        except ErrorDeDominio:
            raise
        except Exception as exc:
            if self.permite_fallback_local:
                logger.warning(
                    "Fallo Gemini; se usa fallback local para continuar el flujo.",
                    exc_info=exc,
                )
                return self._analizar_persona_simulada(
                    imagen_bytes,
                    motivo_error=f"{type(exc).__name__}: {exc}",
                )
            raise ErrorDeDominio(
                "No fue posible conectar con Gemini para analizar la imagen.",
                codigo="gemini_no_disponible",
                estado_http=503,
            ) from exc

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

    def _generar_con_timeout(self, *, imagen_bytes: bytes, mime_type: str, prompt: str, config):
        def ejecutar():
            return self.cliente.models.generate_content(
                model=self.modelo,
                contents=[types.Part.from_bytes(data=imagen_bytes, mime_type=mime_type), prompt],
                config=config,
            )

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(ejecutar)
        try:
            return future.result(timeout=self.timeout_segundos)
        except TiempoExcedidoFuture as exc:
            future.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            if self.permite_fallback_local:
                logger.warning(
                    "Gemini excedio el timeout configurado; se activa fallback local."
                )
                raise TimeoutError(
                    f"Gemini no respondio en {self.timeout_segundos} segundos."
                ) from exc
            raise ErrorDeDominio(
                "Gemini no respondio a tiempo para analizar la imagen.",
                codigo="gemini_timeout",
                estado_http=504,
            ) from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _analizar_persona_simulada(self, imagen_bytes: bytes, motivo_error: str | None = None) -> dict:
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
            "modelo": "gemini-fallback-local" if motivo_error else "gemini-simulado-local",
            "segmentos": respuesta["segmentos"],
            "respuesta_cruda": {
                **respuesta,
                "fallback_local": True,
                "motivo_error": motivo_error,
            },
        }

    def _generar_mascara_local(self, imagen_np: np.ndarray) -> np.ndarray:
        rostro = self._detectar_rostro_principal(imagen_np)
        if rostro is not None:
            mascara = self._generar_mascara_local_guiada_por_rostro(imagen_np, rostro)
            if np.count_nonzero(mascara) > 0:
                return mascara

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

    def _detectar_rostro_principal(self, imagen_np: np.ndarray) -> tuple[int, int, int, int] | None:
        gris = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2GRAY)
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

    def _generar_mascara_local_guiada_por_rostro(
        self, imagen_np: np.ndarray, rostro: tuple[int, int, int, int]
    ) -> np.ndarray:
        alto, ancho = imagen_np.shape[:2]
        x, y, w, h = rostro
        centro_x = x + (w / 2)

        x0 = max(int(centro_x - (w * 1.55)), 0)
        x1 = min(int(centro_x + (w * 1.55)), ancho)
        y0 = max(int(y - (h * 0.45)), 0)
        y1 = min(int(y + (h * 2.15)), alto)

        mascara_gc = np.full((alto, ancho), cv2.GC_BGD, dtype=np.uint8)
        mascara_gc[y0:y1, x0:x1] = cv2.GC_PR_FGD

        margen_cara_x = max(int(w * 0.12), 10)
        margen_cara_y = max(int(h * 0.12), 10)
        cara_x0 = max(x - margen_cara_x, 0)
        cara_y0 = max(y - margen_cara_y, 0)
        cara_x1 = min(x + w + margen_cara_x, ancho)
        cara_y1 = min(y + h + margen_cara_y, alto)
        mascara_gc[cara_y0:cara_y1, cara_x0:cara_x1] = cv2.GC_FGD

        hombros_y0 = min(int(y + (h * 0.9)), alto)
        hombros_y1 = min(int(y + (h * 1.95)), alto)
        hombros_x0 = max(int(centro_x - (w * 1.7)), 0)
        hombros_x1 = min(int(centro_x + (w * 1.7)), ancho)
        if hombros_y1 > hombros_y0 and hombros_x1 > hombros_x0:
            mascara_gc[hombros_y0:hombros_y1, hombros_x0:hombros_x1] = cv2.GC_PR_FGD

        margen_borde = max(min(ancho, alto) // 40, 6)
        mascara_gc[:margen_borde, :] = cv2.GC_BGD
        mascara_gc[-margen_borde:, :] = cv2.GC_BGD
        mascara_gc[:, :margen_borde] = cv2.GC_BGD
        mascara_gc[:, -margen_borde:] = cv2.GC_BGD

        fondo = np.zeros((1, 65), np.float64)
        primer_plano = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(
                imagen_np,
                mascara_gc,
                None,
                fondo,
                primer_plano,
                5,
                cv2.GC_INIT_WITH_MASK,
            )
        except cv2.error:
            return np.zeros((alto, ancho), dtype=np.uint8)

        mascara = np.where(
            (mascara_gc == cv2.GC_FGD) | (mascara_gc == cv2.GC_PR_FGD),
            255,
            0,
        ).astype(np.uint8)

        mascara = self._seleccionar_componente_principal(
            mascara=mascara,
            region_prioritaria=(cara_x0, cara_y0, cara_x1, cara_y1),
        )
        mascara = self._refinar_por_color_de_fondo(
            imagen_np=imagen_np,
            mascara=mascara,
            region_busto=(x0, y0, x1, y1),
            region_rostro=(cara_x0, cara_y0, cara_x1, cara_y1),
        )
        mascara = self._seleccionar_componente_principal(
            mascara=mascara,
            region_prioritaria=(cara_x0, cara_y0, cara_x1, cara_y1),
        )
        kernel = np.ones((5, 5), np.uint8)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel, iterations=2)
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel, iterations=1)
        mascara = cv2.GaussianBlur(mascara, (0, 0), sigmaX=1.35)
        return mascara

    def _seleccionar_componente_principal(
        self,
        *,
        mascara: np.ndarray,
        region_prioritaria: tuple[int, int, int, int],
    ) -> np.ndarray:
        num_etiquetas, etiquetas, estadisticas, _ = cv2.connectedComponentsWithStats(mascara)
        if num_etiquetas <= 1:
            return mascara

        x0, y0, x1, y1 = region_prioritaria
        mejor_etiqueta = None
        mejor_area = 0

        for etiqueta in range(1, num_etiquetas):
            area = int(estadisticas[etiqueta, cv2.CC_STAT_AREA])
            if area <= mejor_area:
                continue

            mascara_etiqueta = etiquetas == etiqueta
            toca_rostro = bool(np.any(mascara_etiqueta[y0:y1, x0:x1]))
            if toca_rostro:
                mejor_etiqueta = etiqueta
                mejor_area = area

        if mejor_etiqueta is None:
            mejor_etiqueta = int(
                1 + np.argmax(estadisticas[1:, cv2.CC_STAT_AREA])
            )

        resultado = np.zeros_like(mascara)
        resultado[etiquetas == mejor_etiqueta] = 255
        return resultado

    def _refinar_por_color_de_fondo(
        self,
        *,
        imagen_np: np.ndarray,
        mascara: np.ndarray,
        region_busto: tuple[int, int, int, int],
        region_rostro: tuple[int, int, int, int],
    ) -> np.ndarray:
        x0, y0, x1, y1 = region_busto
        cara_x0, cara_y0, cara_x1, cara_y1 = region_rostro
        if x1 <= x0 or y1 <= y0:
            return mascara

        alto_caja = y1 - y0
        ancho_caja = x1 - x0
        banda_h = max(int(alto_caja * 0.16), 24)
        banda_w = max(int(ancho_caja * 0.16), 24)

        muestras = [
            imagen_np[y0 : min(y0 + banda_h, y1), x0 : min(x0 + banda_w, x1)],
            imagen_np[y0 : min(y0 + banda_h, y1), max(x1 - banda_w, x0) : x1],
            imagen_np[
                min(y0 + banda_h, y1) : min(y0 + (banda_h * 2), y1),
                x0 : min(x0 + max(banda_w // 2, 12), x1),
            ],
            imagen_np[
                min(y0 + banda_h, y1) : min(y0 + (banda_h * 2), y1),
                max(x1 - max(banda_w // 2, 12), x0) : x1,
            ],
        ]
        muestras = [muestra.reshape(-1, 3) for muestra in muestras if muestra.size]
        if not muestras:
            return mascara

        muestras_np = np.concatenate(muestras, axis=0)
        muestras_lab = cv2.cvtColor(
            muestras_np.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB
        ).reshape(-1, 3)
        color_fondo = np.median(muestras_lab, axis=0)
        distancias_muestra = np.linalg.norm(muestras_lab - color_fondo, axis=1)
        umbral_bajo = max(float(np.percentile(distancias_muestra, 95)) + 4.0, 20.0)
        umbral_alto = max(umbral_bajo + 22.0, 42.0)

        imagen_lab = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2LAB).astype(np.float32)
        distancia_total = np.linalg.norm(imagen_lab - color_fondo, axis=2)
        mascara_color = np.zeros_like(mascara)
        distancia_busto = distancia_total[y0:y1, x0:x1]
        alpha_color = np.clip(
            (distancia_busto - umbral_bajo) / max(umbral_alto - umbral_bajo, 1.0),
            0.0,
            1.0,
        )
        mascara_color[y0:y1, x0:x1] = (alpha_color * 255).astype(np.uint8)
        mascara_color[cara_y0:cara_y1, cara_x0:cara_x1] = 255

        silueta_busto = self._construir_silueta_busto(
            shape=mascara.shape,
            region_busto=region_busto,
            region_rostro=region_rostro,
        )

        refinada = cv2.min(mascara, mascara_color)
        refinada = cv2.bitwise_and(refinada, silueta_busto)
        if np.count_nonzero(refinada) == 0:
            return mascara
        return refinada

    def _construir_silueta_busto(
        self,
        *,
        shape: tuple[int, int],
        region_busto: tuple[int, int, int, int],
        region_rostro: tuple[int, int, int, int],
    ) -> np.ndarray:
        alto, ancho = shape
        silueta = np.zeros((alto, ancho), dtype=np.uint8)
        x0, y0, x1, y1 = region_busto
        cara_x0, cara_y0, cara_x1, cara_y1 = region_rostro

        cara_ancho = max(cara_x1 - cara_x0, 1)
        cara_alto = max(cara_y1 - cara_y0, 1)
        centro_x = int((cara_x0 + cara_x1) / 2)

        centro_cabeza = (centro_x, int(cara_y0 + (cara_alto * 0.62)))
        ejes_cabeza = (
            max(int(cara_ancho * 0.95), 20),
            max(int(cara_alto * 1.18), 26),
        )
        cv2.ellipse(silueta, centro_cabeza, ejes_cabeza, 0, 0, 360, 255, -1)

        hombros_y = min(int(cara_y0 + (cara_alto * 1.95)), alto - 1)
        hombros_alto = max(int(cara_alto * 1.25), 30)
        hombros_ancho = max(int(cara_ancho * 2.15), 40)
        cv2.ellipse(
            silueta,
            (centro_x, hombros_y),
            (hombros_ancho, hombros_alto),
            0,
            0,
            360,
            255,
            -1,
        )

        cuello_x0 = max(int(centro_x - (cara_ancho * 0.52)), 0)
        cuello_x1 = min(int(centro_x + (cara_ancho * 0.52)), ancho)
        cuello_y0 = max(int(cara_y0 + (cara_alto * 0.88)), 0)
        cuello_y1 = min(int(cara_y0 + (cara_alto * 1.75)), alto)
        silueta[cuello_y0:cuello_y1, cuello_x0:cuello_x1] = 255

        silueta[: max(y0 - 4, 0), :] = 0
        silueta[min(y1 + 2, alto) :, :] = 0
        silueta[:, : max(x0 - 8, 0)] = 0
        silueta[:, min(x1 + 8, ancho) :] = 0
        silueta = cv2.GaussianBlur(silueta, (0, 0), sigmaX=2.2)
        return silueta
