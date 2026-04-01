from __future__ import annotations

from django.conf import settings
from django.db import connections
from redis import Redis
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


def verificar_base_de_datos() -> dict:
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1;")
            fila = cursor.fetchone()
        return {"ok": fila == (1,), "detalle": "Base de datos operativa"}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "detalle": str(exc)}


def verificar_redis() -> dict:
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False) and not settings.REDIS_URL:
        return {
            "ok": True,
            "detalle": "Redis omitido en modo local sincrono",
        }
    try:
        cliente = Redis.from_url(settings.REDIS_URL)
        ok = cliente.ping()
        return {"ok": bool(ok), "detalle": "Redis operativo"}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "detalle": str(exc)}


class VistaHealthCheck(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        estado_db = verificar_base_de_datos()
        estado_redis = verificar_redis()
        estado_general = estado_db["ok"] and estado_redis["ok"]
        codigo = 200 if estado_general else 503
        return Response(
            {
                "servicio": "panini-backend",
                "estado": "ok" if estado_general else "degradado",
                "componentes": {
                    "base_de_datos": estado_db,
                    "redis": estado_redis,
                },
            },
            status=codigo,
        )
