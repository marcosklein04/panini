from __future__ import annotations

from rest_framework import status
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.excepciones import ErrorDeDominio


def _normalizar_detalles(detalles):
    if isinstance(detalles, dict):
        return {clave: _normalizar_detalles(valor) for clave, valor in detalles.items()}
    if isinstance(detalles, list):
        return [_normalizar_detalles(valor) for valor in detalles]
    if isinstance(detalles, ErrorDetail):
        return str(detalles)
    return detalles


def _respuesta_error(codigo: str, mensaje: str, campos: dict | None, estado_http: int):
    return Response(
        {"error": {"codigo": codigo, "mensaje": mensaje, "campos": campos or {}}},
        status=estado_http,
    )


def manejador_excepciones_es(exc, context):
    if isinstance(exc, ErrorDeDominio):
        return _respuesta_error(exc.codigo, exc.mensaje, exc.campos, exc.estado_http)

    if isinstance(exc, ValidationError):
        detalles = _normalizar_detalles(exc.detail)
        mensaje = "Hay errores de validacion en la solicitud."
        return _respuesta_error(
            "error_validacion",
            mensaje,
            detalles if isinstance(detalles, dict) else {"no_campo": detalles},
            status.HTTP_400_BAD_REQUEST,
        )

    respuesta = exception_handler(exc, context)
    if respuesta is None:
        return _respuesta_error(
            "error_interno",
            "Ocurrio un error interno inesperado.",
            {},
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    detalles = _normalizar_detalles(respuesta.data)
    mensaje = "No se pudo procesar la solicitud."
    if isinstance(detalles, dict):
        mensaje = detalles.get("detail", mensaje)
        campos = detalles if "detail" not in detalles or len(detalles) > 1 else {}
    else:
        mensaje = detalles
        campos = {}

    return _respuesta_error("error_api", str(mensaje), campos, respuesta.status_code)
