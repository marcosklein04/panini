from __future__ import annotations

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from core.excepciones import ErrorDeDominio
from usuarios.models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ("id", "email", "nombre")


class RegistroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Usuario
        fields = ("id", "email", "nombre", "password")
        read_only_fields = ("id",)

    def validate_email(self, value: str) -> str:
        if Usuario.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese correo.")
        return value.lower().strip()

    def create(self, validated_data):
        password = validated_data.pop("password")
        return Usuario.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        password = attrs["password"]
        usuario = authenticate(
            request=self.context.get("request"), username=email, password=password
        )
        if not usuario:
            raise ErrorDeDominio(
                "Las credenciales ingresadas no son validas.",
                codigo="credenciales_invalidas",
                estado_http=401,
            )
        attrs["usuario"] = usuario
        return attrs


def serializar_tokens(usuario: Usuario) -> dict:
    refresh = RefreshToken.for_user(usuario)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
