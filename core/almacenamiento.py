from __future__ import annotations

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class AlmacenamientoArchivos:
    def guardar_bytes(self, ruta: str, contenido: bytes) -> str:
        return default_storage.save(ruta, ContentFile(contenido))

    def guardar_archivo(self, ruta: str, archivo) -> str:
        return default_storage.save(ruta, archivo)

    def url(self, ruta: str | None) -> str | None:
        if not ruta:
            return None
        return default_storage.url(ruta)

    def abrir(self, ruta: str, modo: str = "rb"):
        return default_storage.open(ruta, modo)
