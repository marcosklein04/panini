from django.contrib import admin

from sesiones.models import SesionProceso


@admin.register(SesionProceso)
class SesionProcesoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "token_publico",
        "trivia",
        "estado",
        "trivia_completada",
        "puede_subir_foto",
        "fecha_actualizacion",
    )
    list_filter = ("estado", "trivia_completada", "puede_subir_foto", "trivia")
    search_fields = ("token_publico", "ip_origen", "user_agent")
