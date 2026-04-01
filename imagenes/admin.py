from django.contrib import admin

from imagenes.models import FotoOriginal, ResultadoRecorte


@admin.register(FotoOriginal)
class FotoOriginalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sesion",
        "mime_type",
        "tamano_bytes",
        "estado",
        "fecha_subida",
    )
    list_filter = ("estado", "mime_type")
    search_fields = ("sesion__token_publico", "nombre_original", "hash_archivo")
    readonly_fields = ("hash_archivo", "metadata", "mensaje_error")


@admin.register(ResultadoRecorte)
class ResultadoRecorteAdmin(admin.ModelAdmin):
    list_display = ("id", "foto_original", "estado", "modelo_gemini", "fecha_fin_procesamiento")
    list_filter = ("estado", "modelo_gemini", "proveedor_ia")
    search_fields = ("foto_original__nombre_original", "celery_task_id")
    readonly_fields = ("metadatos_recorte", "errores", "celery_task_id")
