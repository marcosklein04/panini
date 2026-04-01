from rest_framework import serializers

from catalogos.models import Equipo


class EquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipo
        fields = ("id", "nombre", "slug", "pais")
