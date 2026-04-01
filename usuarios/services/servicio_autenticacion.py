from rest_framework_simplejwt.tokens import RefreshToken


class ServicioAutenticacion:
    @staticmethod
    def generar_tokens_para_usuario(usuario) -> dict:
        refresh = RefreshToken.for_user(usuario)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}
