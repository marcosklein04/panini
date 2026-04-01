from django.contrib import admin

from trivias.models import DatosSticker, OpcionRespuesta, PreguntaTrivia, RespuestaTrivia, Trivia


class OpcionRespuestaInline(admin.TabularInline):
    model = OpcionRespuesta
    extra = 0


@admin.register(Trivia)
class TriviaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa", "creado_en")
    list_filter = ("activa",)
    search_fields = ("nombre",)


@admin.register(PreguntaTrivia)
class PreguntaTriviaAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "texto",
        "trivia",
        "tipo_respuesta",
        "obligatoria",
        "orden",
        "activa",
    )
    list_filter = ("trivia", "tipo_respuesta", "obligatoria", "activa")
    search_fields = ("codigo", "texto", "placeholder")
    ordering = ("trivia", "orden")
    inlines = [OpcionRespuestaInline]


@admin.register(RespuestaTrivia)
class RespuestaTriviaAdmin(admin.ModelAdmin):
    list_display = ("sesion", "pregunta", "valor_texto", "valor_numero", "valor_equipo")
    list_filter = ("pregunta__codigo",)
    search_fields = ("sesion__token_publico", "pregunta__codigo", "valor_texto")
    list_select_related = ("sesion", "pregunta", "valor_equipo", "valor_opcion")


@admin.register(DatosSticker)
class DatosStickerAdmin(admin.ModelAdmin):
    list_display = ("sesion", "nombre", "apellido", "equipo", "altura_cm", "peso_kg")
    search_fields = ("sesion__token_publico", "nombre", "apellido", "equipo")
    list_select_related = ("sesion", "equipo_catalogo")
