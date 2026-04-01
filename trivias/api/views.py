from rest_framework.response import Response
from rest_framework.views import APIView

from trivias.api.serializers import TriviaActivaSerializer
from trivias.services.servicio_trivia import ServicioTrivia


class VistaTriviaActivaAPIView(APIView):
    def get(self, request):
        trivia = ServicioTrivia.obtener_trivia_activa()
        return Response(TriviaActivaSerializer(trivia).data)
