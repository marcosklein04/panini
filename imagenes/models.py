from __future__ import annotations

from pathlib import Path

from django.db import models

from core.enums import EstadoProceso, ProveedorIA
from core.modelos import ModeloBaseUUID


def ruta_foto_original(instancia, nombre_archivo: str) -> str:
    extension = Path(nombre_archivo).suffix.lower() or ".jpg"
    return f"fotos/originales/{instancia.sesion_id}/{instancia.id}{extension}"


def ruta_recorte(instancia, nombre_archivo: str) -> str:
    return f"fotos/recortes/{instancia.foto_original.sesion_id}/{instancia.id}.png"


def ruta_mascara(instancia, nombre_archivo: str) -> str:
    return f"fotos/mascaras/{instancia.foto_original.sesion_id}/{instancia.id}.png"


class FotoOriginal(ModeloBaseUUID):
    sesion = models.ForeignKey(
        "sesiones.SesionProceso",
        on_delete=models.CASCADE,
        related_name="fotos",
        verbose_name="Sesion",
    )
    archivo = models.ImageField(upload_to=ruta_foto_original, verbose_name="Archivo")
    nombre_original = models.CharField(max_length=255, verbose_name="Nombre original")
    mime_type = models.CharField(max_length=100, verbose_name="Mime type")
    tamano_bytes = models.PositiveIntegerField(verbose_name="Tamano en bytes")
    ancho = models.PositiveIntegerField(verbose_name="Ancho")
    alto = models.PositiveIntegerField(verbose_name="Alto")
    hash_archivo = models.CharField(max_length=64, db_index=True, verbose_name="Hash SHA256")
    estado = models.CharField(
        max_length=20,
        choices=EstadoProceso.choices,
        default=EstadoProceso.PENDIENTE,
        verbose_name="Estado",
    )
    mensaje_error = models.TextField(blank=True, verbose_name="Mensaje de error")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de subida")

    class Meta:
        verbose_name = "Foto original"
        verbose_name_plural = "Fotos originales"
        ordering = ["-fecha_subida"]

    def __str__(self) -> str:
        return f"{self.nombre_original} ({self.id})"


class ResultadoRecorte(ModeloBaseUUID):
    foto_original = models.OneToOneField(
        FotoOriginal,
        on_delete=models.CASCADE,
        related_name="resultado_recorte",
        verbose_name="Foto original",
    )
    proveedor_ia = models.CharField(
        max_length=20,
        choices=ProveedorIA.choices,
        default=ProveedorIA.GEMINI,
        verbose_name="Proveedor de IA",
    )
    png_transparente = models.ImageField(
        upload_to=ruta_recorte,
        null=True,
        blank=True,
        verbose_name="PNG transparente",
    )
    archivo_mascara = models.ImageField(
        upload_to=ruta_mascara,
        null=True,
        blank=True,
        verbose_name="Archivo mascara",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoProceso.choices,
        default=EstadoProceso.PENDIENTE,
        verbose_name="Estado",
    )
    celery_task_id = models.CharField(
        max_length=255, blank=True, verbose_name="ID de tarea Celery"
    )
    modelo_gemini = models.CharField(max_length=120, blank=True, verbose_name="Modelo Gemini")
    metadatos_recorte = models.JSONField(default=dict, blank=True, verbose_name="Metadatos")
    errores = models.TextField(blank=True, verbose_name="Errores")
    tiempo_procesamiento = models.FloatField(
        null=True, blank=True, verbose_name="Tiempo de procesamiento"
    )
    fecha_inicio_procesamiento = models.DateTimeField(
        null=True, blank=True, verbose_name="Inicio de procesamiento"
    )
    fecha_fin_procesamiento = models.DateTimeField(
        null=True, blank=True, verbose_name="Fin de procesamiento"
    )

    class Meta:
        verbose_name = "Resultado de recorte"
        verbose_name_plural = "Resultados de recorte"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"Recorte {self.id}"
