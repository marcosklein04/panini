from __future__ import annotations

from rest_framework import serializers

from figuritas.models import FiguritaGenerada


class GenerarFiguritaSesionSerializer(serializers.Serializer):
    resultado_recorte_id = serializers.UUIDField(required=False)
    plantilla_id = serializers.UUIDField(required=False)


class FiguritaGeneradaSerializer(serializers.ModelSerializer):
    imagen_final_url = serializers.SerializerMethodField()
    imagen_preview_url = serializers.SerializerMethodField()

    class Meta:
        model = FiguritaGenerada
        fields = (
            "id",
            "estado",
            "celery_task_id",
            "mensaje_error",
            "metadata",
            "imagen_final_url",
            "imagen_preview_url",
            "fecha_generacion",
            "plantilla_id",
            "resultado_recorte_id",
            "nombre_mostrado",
            "datos_renderizados",
        )

    def get_imagen_final_url(self, obj):
        return obj.imagen_final.url if obj.imagen_final else None

    def get_imagen_preview_url(self, obj):
        return obj.imagen_preview.url if obj.imagen_preview else None
