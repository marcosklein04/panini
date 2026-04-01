from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.throttling import ThrottleLogin, ThrottleRegistro
from usuarios.api.serializers import (
    LoginSerializer,
    RegistroSerializer,
    UsuarioSerializer,
    serializar_tokens,
)


class VistaRegistroAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ThrottleRegistro]

    def post(self, request):
        serializer = RegistroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return Response(
            {
                "mensaje": "Usuario registrado correctamente.",
                "usuario": UsuarioSerializer(usuario).data,
                "tokens": serializar_tokens(usuario),
            },
            status=201,
        )


class VistaLoginAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ThrottleLogin]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        usuario = serializer.validated_data["usuario"]
        return Response(
            {
                "mensaje": "Inicio de sesion exitoso.",
                "usuario": UsuarioSerializer(usuario).data,
                "tokens": serializar_tokens(usuario),
            }
        )
