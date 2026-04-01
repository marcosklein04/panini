from __future__ import annotations

from django.db import models
from django.utils.text import slugify

from core.modelos import ModeloBaseUUID


class Equipo(ModeloBaseUUID):
    nombre = models.CharField(max_length=120, unique=True, verbose_name="Nombre")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    pais = models.CharField(max_length=120, blank=True, verbose_name="Pais")
    orden = models.PositiveIntegerField(default=1, verbose_name="Orden")
    activa = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["orden", "nombre"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.nombre
