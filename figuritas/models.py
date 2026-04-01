from __future__ import annotations

from pathlib import Path

from django.db import models
from django.db.models import Q

from core.enums import EstadoProceso
from core.modelos import ModeloBaseUUID


def ruta_asset_plantilla(instancia, nombre_archivo: str) -> str:
    extension = Path(nombre_archivo).suffix.lower() or ".png"
    return f"figuritas/plantillas/{instancia.slug}{extension}"


def ruta_figurita_final(instancia, nombre_archivo: str) -> str:
    return f"figuritas/generadas/{instancia.sesion_id}/{instancia.id}.png"


def ruta_figurita_preview(instancia, nombre_archivo: str) -> str:
    return f"figuritas/previews/{instancia.sesion_id}/{instancia.id}.jpg"


class PlantillaFigurita(ModeloBaseUUID):
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    predeterminada = models.BooleanField(default=False, verbose_name="Predeterminada")
    configuracion_visual = models.JSONField(
        default=dict, blank=True, verbose_name="Configuracion visual"
    )
    archivo_base = models.ImageField(
        upload_to=ruta_asset_plantilla,
        null=True,
        blank=True,
        verbose_name="Archivo base",
    )

    class Meta:
        verbose_name = "Plantilla de figurita"
        verbose_name_plural = "Plantillas de figurita"
        constraints = [
            models.UniqueConstraint(
                fields=("predeterminada",),
                condition=Q(predeterminada=True),
                name="plantilla_predeterminada_unica",
            )
        ]
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class FiguritaGenerada(ModeloBaseUUID):
    sesion = models.ForeignKey(
        "sesiones.SesionProceso",
        on_delete=models.CASCADE,
        related_name="figuritas",
        verbose_name="Sesion",
    )
    plantilla = models.ForeignKey(
        PlantillaFigurita,
        on_delete=models.PROTECT,
        related_name="figuritas_generadas",
        verbose_name="Plantilla",
    )
    resultado_recorte = models.ForeignKey(
        "imagenes.ResultadoRecorte",
        on_delete=models.CASCADE,
        related_name="figuritas",
        verbose_name="Resultado de recorte",
    )
    imagen_final = models.ImageField(
        upload_to=ruta_figurita_final,
        null=True,
        blank=True,
        verbose_name="Imagen final",
    )
    imagen_preview = models.ImageField(
        upload_to=ruta_figurita_preview,
        null=True,
        blank=True,
        verbose_name="Imagen preview",
    )
    nombre_mostrado = models.CharField(max_length=200, blank=True, verbose_name="Nombre mostrado")
    datos_renderizados = models.JSONField(
        default=dict, blank=True, verbose_name="Datos renderizados"
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
    mensaje_error = models.TextField(blank=True, verbose_name="Mensaje de error")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadata")
    fecha_generacion = models.DateTimeField(
        null=True, blank=True, verbose_name="Fecha de generacion"
    )

    class Meta:
        verbose_name = "Figurita generada"
        verbose_name_plural = "Figuritas generadas"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return f"{self.id} - {self.plantilla.nombre}"
