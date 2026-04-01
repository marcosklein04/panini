from rest_framework.response import Response
from rest_framework.views import APIView

from core.throttling import ThrottleSesionIniciar, ThrottleSesionResponder
from sesiones.api.serializers import IniciarSesionSerializer, ResponderSesionSerializer
from sesiones.services.servicio_sesiones import ServicioSesiones
from trivias.api.serializers import PreguntaTriviaPublicaSerializer
from trivias.services.servicio_trivia import ServicioTrivia


class VistaIniciarSesionAPIView(APIView):
    throttle_classes = [ThrottleSesionIniciar]

    def post(self, request):
        serializer = IniciarSesionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sesion, creada = ServicioSesiones.iniciar_o_reanudar(
            token_publico=serializer.validated_data.get("token_publico"),
            request=request,
        )
        return Response(
            {
                "mensaje": "Sesion iniciada correctamente." if creada else "Sesion reanudada correctamente.",
                "sesion": ServicioSesiones.obtener_estado_serializado(sesion),
                "fue_creada": creada,
            },
            status=201 if creada else 200,
        )


class VistaPreguntasSesionAPIView(APIView):
    def get(self, request, token_publico):
        sesion = ServicioSesiones.obtener_sesion_por_token(token_publico=token_publico)
        preguntas = ServicioTrivia.obtener_preguntas_sesion(sesion)
        respuestas = {
            str(respuesta.pregunta_id): respuesta
            for respuesta in sesion.respuestas.select_related("valor_opcion", "valor_equipo")
        }
        return Response(
            {
                "trivia": {
                    "id": sesion.trivia_id,
                    "nombre": sesion.trivia.nombre,
                    "descripcion": sesion.trivia.descripcion,
                },
                "preguntas": PreguntaTriviaPublicaSerializer(
                    preguntas,
                    many=True,
                    context={"respuestas": respuestas},
                ).data,
            }
        )


class VistaResponderSesionAPIView(APIView):
    throttle_classes = [ThrottleSesionResponder]

    def post(self, request, token_publico):
        serializer = ResponderSesionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sesion = ServicioSesiones.obtener_sesion_por_token(token_publico=token_publico)
        sesion, datos_sticker, respuestas_guardadas, evaluacion = ServicioTrivia.responder_sesion(
            sesion=sesion,
            payload=serializer.validated_data,
        )
        return Response(
            {
                "mensaje": "Respuesta registrada correctamente.",
                "respuestas_guardadas": len(respuestas_guardadas),
                "evaluacion": evaluacion,
                "sesion": ServicioSesiones.obtener_estado_serializado(sesion),
            }
        )


class VistaEstadoSesionAPIView(APIView):
    def get(self, request, token_publico):
        sesion = ServicioSesiones.obtener_sesion_por_token(token_publico=token_publico)
        return Response(ServicioSesiones.obtener_estado_serializado(sesion))
