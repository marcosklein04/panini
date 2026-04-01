import threading

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from core.excepciones import ErrorDeDominio
from core.throttling import ThrottleProcesamientoImagen, ThrottleSubidaImagen
from imagenes.api.serializers import (
    FotoOriginalSerializer,
    ProcesarImagenSerializer,
    ResultadoRecorteSerializer,
    SubirImagenSerializer,
)
from imagenes.models import ResultadoRecorte
from imagenes.services.servicio_recorte_imagen import ServicioRecorteImagen
from imagenes.tasks import tarea_procesar_imagen
from sesiones.services.servicio_sesiones import ServicioSesiones


def _procesar_imagen_en_segundo_plano(*, foto_id: str, plantilla_id: str | None = None) -> None:
    try:
        ServicioRecorteImagen.procesar_foto(
            foto_id=foto_id,
            plantilla_id=plantilla_id,
            task_id=f"local-{foto_id}",
        )
    except Exception:
        # El servicio ya persiste el error en base de datos.
        return


class VistaSubirImagenAPIView(APIView):
    throttle_classes = [ThrottleSubidaImagen]

    def post(self, request, token_publico):
        serializer = SubirImagenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sesion = ServicioSesiones.obtener_sesion_por_token(token_publico=token_publico)
        foto = ServicioRecorteImagen.guardar_foto_original(
            sesion=sesion,
            archivo=serializer.validated_data["archivo"],
        )
        return Response(
            {
                "mensaje": "Imagen subida correctamente.",
                "foto": FotoOriginalSerializer(foto).data,
            },
            status=201,
        )


class VistaProcesarImagenAPIView(APIView):
    throttle_classes = [ThrottleProcesamientoImagen]

    def post(self, request, foto_id):
        serializer = ProcesarImagenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sesion = ServicioSesiones.obtener_sesion_por_token(
            token_publico=serializer.validated_data["token_publico"]
        )
        foto = ServicioRecorteImagen.obtener_foto(foto_id=foto_id)
        ServicioSesiones.validar_foto_pertenece_a_sesion(sesion=sesion, foto=foto)
        resultado, ya_existente = ServicioRecorteImagen.preparar_procesamiento(foto=foto)
        if ya_existente:
            return Response(
                {
                    "mensaje": "La imagen ya tiene un recorte completado.",
                    "resultado": ResultadoRecorteSerializer(resultado).data,
                }
            )

        if settings.CELERY_TASK_ALWAYS_EAGER:
            plantilla_id = (
                str(serializer.validated_data["plantilla_id"])
                if serializer.validated_data.get("plantilla_id")
                else None
            )
            resultado = ServicioRecorteImagen.registrar_tarea(
                resultado=resultado,
                task_id=f"local-{foto.id}",
            )
            hilo = threading.Thread(
                target=_procesar_imagen_en_segundo_plano,
                kwargs={"foto_id": str(foto.id), "plantilla_id": plantilla_id},
                daemon=True,
                name=f"procesamiento-foto-{foto.id}",
            )
            hilo.start()
            return Response(
                {
                    "mensaje": "Procesamiento de imagen iniciado correctamente.",
                    "resultado": ResultadoRecorteSerializer(resultado).data,
                },
                status=202,
            )

        try:
            tarea = tarea_procesar_imagen.delay(
                str(foto.id),
                str(serializer.validated_data["plantilla_id"])
                if serializer.validated_data.get("plantilla_id")
                else None,
            )
        except Exception as exc:
            raise ErrorDeDominio(
                "No se pudo encolar el procesamiento de la imagen.",
                codigo="cola_no_disponible",
                estado_http=503,
            ) from exc

        resultado = ServicioRecorteImagen.registrar_tarea(resultado=resultado, task_id=tarea.id)
        resultado.refresh_from_db()
        return Response(
            {
                "mensaje": "Procesamiento de imagen encolado correctamente.",
                "resultado": ResultadoRecorteSerializer(resultado).data,
            },
            status=202,
        )


class VistaResultadoImagenAPIView(APIView):
    def get(self, request, foto_id):
        foto = ServicioRecorteImagen.obtener_foto(foto_id=foto_id)
        try:
            resultado = ResultadoRecorte.objects.get(foto_original=foto)
        except ResultadoRecorte.DoesNotExist as exc:
            raise ErrorDeDominio(
                "La imagen aun no tiene un resultado de recorte.",
                codigo="resultado_no_disponible",
                estado_http=404,
            ) from exc
        return Response(ResultadoRecorteSerializer(resultado).data)
