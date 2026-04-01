from django.contrib import admin

from catalogos.models import Equipo


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "pais", "orden", "activa")
    list_filter = ("activa", "pais")
    search_fields = ("nombre", "pais", "slug")
    ordering = ("orden", "nombre")
