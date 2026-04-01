from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from usuarios.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    ordering = ("email",)
    list_display = ("email", "nombre", "is_staff", "is_active", "creado_en")
    list_filter = ("is_staff", "is_active", "is_superuser")
    search_fields = ("email", "nombre")
    readonly_fields = ("last_login", "creado_en", "actualizado_en")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informacion personal", {"fields": ("nombre",)}),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Fechas", {"fields": ("last_login", "creado_en", "actualizado_en")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nombre", "password1", "password2", "is_staff"),
            },
        ),
    )
