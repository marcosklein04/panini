from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from core.excepciones import ErrorDeDominio
from core.throttling import ThrottleGeneracionFigurita
from figuritas.api.serializers import GenerarFiguritaSesionSerializer, FiguritaGeneradaSerializer
from figuritas.services.servicio_composicion_figurita import ServicioComposicionFigurita
from figuritas.tasks import tarea_generar_figurita
from imagenes.models import ResultadoRecorte
from sesiones.services.servicio_sesiones import ServicioSesiones


class VistaGenerarFiguritaSesionAPIView(APIView):
    throttle_classes = [ThrottleGeneracionFigurita]

    def post(self, request, token_publico):
        serializer = GenerarFiguritaSesionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sesion = ServicioSesiones.obtener_sesion_por_token(token_publico=token_publico)

        resultado = None
        if serializer.validated_data.get("resultado_recorte_id"):
            try:
                resultado = ResultadoRecorte.objects.select_related(
                    "foto_original",
                    "foto_original__sesion",
                    "foto_original__sesion__datos_sticker",
                ).get(id=serializer.validated_data["resultado_recorte_id"])
            except ResultadoRecorte.DoesNotExist as exc:
                raise ErrorDeDominio(
                    "No se encontro el resultado de recorte indicado.",
                    codigo="recorte_no_encontrado",
                    estado_http=404,
                ) from exc
        else:
            resultado = (
                ResultadoRecorte.objects.select_related(
                    "foto_original",
                    "foto_original__sesion",
                    "foto_original__sesion__datos_sticker",
                )
                .filter(foto_original__sesion=sesion, estado="completado")
                .order_by("-creado_en")
                .first()
            )
            if not resultado:
                raise ErrorDeDominio(
                    "La sesion aun no tiene un recorte completado para generar la figurita.",
                    codigo="recorte_no_disponible",
                    estado_http=409,
                )

        ServicioSesiones.validar_recorte_pertenece_a_sesion(
            sesion=sesion,
            resultado_recorte=resultado,
        )
        figurita = ServicioComposicionFigurita.crear_registro_pendiente(
            resultado_recorte=resultado,
            plantilla_id=serializer.validated_data.get("plantilla_id"),
        )
        if settings.CELERY_TASK_ALWAYS_EAGER:
            figurita = ServicioComposicionFigurita.generar_figurita(figurita_id=str(figurita.id))
            return Response(
                {
                    "mensaje": "Generacion de figurita completada correctamente.",
                    "figurita": FiguritaGeneradaSerializer(figurita).data,
                },
                status=202,
            )
        try:
            tarea = tarea_generar_figurita.delay(str(figurita.id))
        except Exception as exc:
            raise ErrorDeDominio(
                "No se pudo encolar la generacion de la figurita.",
                codigo="cola_no_disponible",
                estado_http=503,
            ) from exc
        figurita = ServicioComposicionFigurita.registrar_tarea(
            figurita=figurita, task_id=tarea.id
        )
        figurita.refresh_from_db()
        return Response(
            {
                "mensaje": "Generacion de figurita encolada correctamente.",
                "figurita": FiguritaGeneradaSerializer(figurita).data,
            },
            status=202,
        )


class VistaDetalleFiguritaAPIView(APIView):
    def get(self, request, figurita_id):
        figurita = ServicioComposicionFigurita.obtener_figurita_publica(
            figurita_id=figurita_id
        )
        return Response(FiguritaGeneradaSerializer(figurita).data)
