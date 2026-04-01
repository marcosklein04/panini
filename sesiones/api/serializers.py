from rest_framework import serializers


class IniciarSesionSerializer(serializers.Serializer):
    token_publico = serializers.UUIDField(required=False)


class RespuestaSesionItemSerializer(serializers.Serializer):
    pregunta_id = serializers.UUIDField()
    valor = serializers.JSONField(required=False)
    opcion_id = serializers.UUIDField(required=False)
    equipo_id = serializers.UUIDField(required=False)

    def validate(self, attrs):
        if (
            attrs.get("valor") in (None, "")
            and not attrs.get("opcion_id")
            and not attrs.get("equipo_id")
        ):
            raise serializers.ValidationError(
                "Debes enviar un valor, una opcion o un equipo para responder."
            )
        return attrs


class ResponderSesionSerializer(serializers.Serializer):
    pregunta_id = serializers.UUIDField(required=False)
    valor = serializers.JSONField(required=False)
    opcion_id = serializers.UUIDField(required=False)
    equipo_id = serializers.UUIDField(required=False)
    respuestas = RespuestaSesionItemSerializer(many=True, required=False)

    def validate(self, attrs):
        if attrs.get("respuestas"):
            return attrs
        if not attrs.get("pregunta_id"):
            raise serializers.ValidationError(
                "Debes enviar una respuesta individual o un arreglo de respuestas."
            )
        if (
            attrs.get("valor") in (None, "")
            and not attrs.get("opcion_id")
            and not attrs.get("equipo_id")
        ):
            raise serializers.ValidationError(
                "Debes enviar un valor, una opcion o un equipo para responder."
            )
        return attrs
