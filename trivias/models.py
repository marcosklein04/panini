from __future__ import annotations

from django.db import models

from core.enums import CampoSticker, TipoRespuestaTrivia
from core.modelos import ModeloBaseUUID


class Trivia(ModeloBaseUUID):
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripcion")
    activa = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Flujo de trivia"
        verbose_name_plural = "Flujos de trivia"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        return self.nombre


class PreguntaTrivia(ModeloBaseUUID):
    trivia = models.ForeignKey(
        Trivia,
        on_delete=models.CASCADE,
        related_name="preguntas",
        verbose_name="Trivia",
    )
    codigo = models.CharField(max_length=50, verbose_name="Codigo")
    texto = models.CharField(max_length=255, verbose_name="Texto")
    tipo_respuesta = models.CharField(
        max_length=30,
        choices=TipoRespuestaTrivia.choices,
        verbose_name="Tipo de respuesta",
    )
    orden = models.PositiveIntegerField(default=1, verbose_name="Orden")
    obligatoria = models.BooleanField(default=True, verbose_name="Obligatoria")
    placeholder = models.CharField(max_length=255, blank=True, verbose_name="Placeholder")
    ayuda = models.TextField(blank=True, verbose_name="Ayuda")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    mapea_a_campo_sticker = models.CharField(
        max_length=40,
        choices=CampoSticker.choices,
        verbose_name="Mapea a campo del sticker",
    )
    reglas_validacion = models.JSONField(default=dict, blank=True, verbose_name="Reglas")

    class Meta:
        verbose_name = "Pregunta de trivia"
        verbose_name_plural = "Preguntas de trivia"
        ordering = ["orden", "creado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=("trivia", "codigo"), name="pregunta_trivia_codigo_unico"
            )
        ]

    def __str__(self) -> str:
        return f"{self.trivia.nombre} - {self.codigo}"


class OpcionRespuesta(ModeloBaseUUID):
    pregunta = models.ForeignKey(
        PreguntaTrivia,
        on_delete=models.CASCADE,
        related_name="opciones",
        verbose_name="Pregunta",
    )
    valor = models.CharField(max_length=120, verbose_name="Valor")
    etiqueta = models.CharField(max_length=120, verbose_name="Etiqueta")
    orden = models.PositiveIntegerField(default=1, verbose_name="Orden")
    activa = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        verbose_name = "Opcion de respuesta"
        verbose_name_plural = "Opciones de respuesta"
        ordering = ["orden", "creado_en"]

    def __str__(self) -> str:
        return self.etiqueta


class RespuestaTrivia(ModeloBaseUUID):
    sesion = models.ForeignKey(
        "sesiones.SesionProceso",
        on_delete=models.CASCADE,
        related_name="respuestas",
        verbose_name="Sesion",
    )
    pregunta = models.ForeignKey(
        PreguntaTrivia,
        on_delete=models.CASCADE,
        related_name="respuestas",
        verbose_name="Pregunta",
    )
    valor_texto = models.CharField(
        max_length=255, blank=True, verbose_name="Valor de texto"
    )
    valor_numero = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Valor numerico",
    )
    valor_fecha = models.DateField(null=True, blank=True, verbose_name="Valor fecha")
    valor_opcion = models.ForeignKey(
        OpcionRespuesta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="respuestas",
        verbose_name="Valor de opcion",
    )
    valor_equipo = models.ForeignKey(
        "catalogos.Equipo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="respuestas_trivia",
        verbose_name="Valor de equipo",
    )
    respondida_en = models.DateTimeField(auto_now=True, verbose_name="Respondida en")

    class Meta:
        verbose_name = "Respuesta de trivia"
        verbose_name_plural = "Respuestas de trivia"
        ordering = ["pregunta__orden", "creado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=("sesion", "pregunta"), name="respuesta_unica_por_sesion_pregunta"
            )
        ]

    def __str__(self) -> str:
        return f"{self.sesion_id} - {self.pregunta.codigo}"


class DatosSticker(ModeloBaseUUID):
    sesion = models.OneToOneField(
        "sesiones.SesionProceso",
        on_delete=models.CASCADE,
        related_name="datos_sticker",
        verbose_name="Sesion",
    )
    nombre = models.CharField(max_length=100, blank=True, verbose_name="Nombre")
    apellido = models.CharField(max_length=100, blank=True, verbose_name="Apellido")
    fecha_nacimiento = models.DateField(
        null=True, blank=True, verbose_name="Fecha de nacimiento"
    )
    altura_cm = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Altura en cm"
    )
    peso_kg = models.PositiveIntegerField(null=True, blank=True, verbose_name="Peso en kg")
    equipo = models.CharField(max_length=120, blank=True, verbose_name="Equipo")
    equipo_catalogo = models.ForeignKey(
        "catalogos.Equipo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stickers_normalizados",
        verbose_name="Equipo del catalogo",
    )
    apodo = models.CharField(max_length=100, blank=True, verbose_name="Apodo")
    posicion = models.CharField(max_length=100, blank=True, verbose_name="Posicion")
    nacionalidad = models.CharField(
        max_length=100, blank=True, verbose_name="Nacionalidad"
    )

    class Meta:
        verbose_name = "Datos del sticker"
        verbose_name_plural = "Datos de stickers"
        ordering = ["-creado_en"]

    def __str__(self) -> str:
        nombre_completo = f"{self.nombre} {self.apellido}".strip()
        return nombre_completo or str(self.sesion.token_publico)
