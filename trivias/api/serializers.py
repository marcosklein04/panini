from __future__ import annotations

from rest_framework import serializers

from trivias.models import DatosSticker, OpcionRespuesta, PreguntaTrivia, RespuestaTrivia, Trivia


class OpcionRespuestaPublicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpcionRespuesta
        fields = ("id", "valor", "etiqueta", "orden")


class DatosStickerSerializer(serializers.ModelSerializer):
    equipo_id = serializers.SerializerMethodField()

    class Meta:
        model = DatosSticker
        fields = (
            "nombre",
            "apellido",
            "fecha_nacimiento",
            "altura_cm",
            "peso_kg",
            "equipo",
            "equipo_id",
            "apodo",
            "posicion",
            "nacionalidad",
        )

    def get_equipo_id(self, obj):
        return obj.equipo_catalogo_id


class PreguntaTriviaPublicaSerializer(serializers.ModelSerializer):
    opciones = OpcionRespuestaPublicaSerializer(many=True, read_only=True)
    respuesta_actual = serializers.SerializerMethodField()

    class Meta:
        model = PreguntaTrivia
        fields = (
            "id",
            "codigo",
            "texto",
            "tipo_respuesta",
            "orden",
            "obligatoria",
            "placeholder",
            "ayuda",
            "mapea_a_campo_sticker",
            "reglas_validacion",
            "opciones",
            "respuesta_actual",
        )

    def get_respuesta_actual(self, obj):
        respuestas = self.context.get("respuestas") or {}
        respuesta = respuestas.get(obj.id) or respuestas.get(str(obj.id))
        if not respuesta:
            return None
        return serializar_respuesta_actual(respuesta)


class TriviaActivaSerializer(serializers.ModelSerializer):
    preguntas = PreguntaTriviaPublicaSerializer(many=True, read_only=True)

    class Meta:
        model = Trivia
        fields = ("id", "nombre", "descripcion", "preguntas")


def serializar_respuesta_actual(respuesta: RespuestaTrivia) -> dict:
    if respuesta.valor_equipo_id:
        return {
            "equipo_id": respuesta.valor_equipo_id,
            "valor": respuesta.valor_equipo.nombre,
            "tipo": "equipo",
        }
    if respuesta.valor_opcion_id:
        return {
            "opcion_id": respuesta.valor_opcion_id,
            "valor": respuesta.valor_opcion.etiqueta,
            "tipo": "opcion",
        }
    if respuesta.valor_fecha:
        return {"valor": respuesta.valor_fecha.isoformat(), "tipo": "fecha"}
    if respuesta.valor_numero is not None:
        return {"valor": int(respuesta.valor_numero), "tipo": "numero"}
    return {"valor": respuesta.valor_texto, "tipo": "texto"}
