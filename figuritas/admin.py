from django.contrib import admin

from figuritas.models import FiguritaGenerada, PlantillaFigurita


@admin.register(PlantillaFigurita)
class PlantillaFiguritaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activa", "predeterminada")
    list_filter = ("activa", "predeterminada")
    search_fields = ("nombre", "slug")


@admin.register(FiguritaGenerada)
class FiguritaGeneradaAdmin(admin.ModelAdmin):
    list_display = ("id", "sesion", "plantilla", "nombre_mostrado", "estado", "fecha_generacion")
    list_filter = ("estado", "plantilla")
    search_fields = ("sesion__token_publico", "plantilla__nombre", "celery_task_id")
    readonly_fields = ("metadata", "mensaje_error", "datos_renderizados")
