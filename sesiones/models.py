from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from core.enums import EstadoProceso
from core.modelos import ModeloBaseUUID


class SesionProceso(ModeloBaseUUID):
    trivia = models.ForeignKey(
        "trivias.Trivia",
        on_delete=models.PROTECT,
        related_name="sesiones",
        verbose_name="Trivia",
    )
    token_publico = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        verbose_name="Token publico",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoProceso.choices,
        default=EstadoProceso.PENDIENTE,
        verbose_name="Estado",
    )
    trivia_completada = models.BooleanField(default=False, verbose_name="Trivia completada")
    puede_subir_foto = models.BooleanField(default=False, verbose_name="Puede subir foto")
    fecha_inicio = models.DateTimeField(default=timezone.now, verbose_name="Fecha de inicio")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualizacion")
    fecha_fin = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de fin")
    ip_origen = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="IP de origen"
    )
    user_agent = models.CharField(max_length=500, blank=True, verbose_name="User agent")

    class Meta:
        verbose_name = "Sesion de proceso"
        verbose_name_plural = "Sesiones de proceso"
        ordering = ["-fecha_inicio"]

    def __str__(self) -> str:
        return str(self.token_publico)
