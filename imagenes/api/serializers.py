from __future__ import annotations

from rest_framework import serializers

from imagenes.models import FotoOriginal, ResultadoRecorte


class FotoOriginalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoOriginal
        fields = (
            "id",
            "nombre_original",
            "mime_type",
            "tamano_bytes",
            "ancho",
            "alto",
            "estado",
            "mensaje_error",
            "metadata",
            "fecha_subida",
        )


class SubirImagenSerializer(serializers.Serializer):
    archivo = serializers.ImageField()


class ProcesarImagenSerializer(serializers.Serializer):
    token_publico = serializers.UUIDField()
    plantilla_id = serializers.UUIDField(required=False)


class ResultadoRecorteSerializer(serializers.ModelSerializer):
    png_transparente_url = serializers.SerializerMethodField()
    archivo_mascara_url = serializers.SerializerMethodField()

    class Meta:
        model = ResultadoRecorte
        fields = (
            "id",
            "estado",
            "proveedor_ia",
            "celery_task_id",
            "modelo_gemini",
            "errores",
            "metadatos_recorte",
            "png_transparente_url",
            "archivo_mascara_url",
            "tiempo_procesamiento",
            "fecha_inicio_procesamiento",
            "fecha_fin_procesamiento",
        )

    def get_png_transparente_url(self, obj):
        return obj.png_transparente.url if obj.png_transparente else None

    def get_archivo_mascara_url(self, obj):
        return obj.archivo_mascara.url if obj.archivo_mascara else None
