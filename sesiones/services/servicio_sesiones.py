from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from core.enums import EstadoProceso
from core.excepciones import ErrorDeDominio
from sesiones.models import SesionProceso


class ServicioSesiones:
    @staticmethod
    def _extraer_ip(request) -> str:
        encabezado = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if encabezado:
            return encabezado.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    @staticmethod
    def _extraer_user_agent(request) -> str:
        return request.META.get("HTTP_USER_AGENT", "")[:500]

    @staticmethod
    @transaction.atomic
    def iniciar_o_reanudar(*, token_publico=None, request):
        from trivias.services.servicio_trivia import ServicioTrivia

        trivia = ServicioTrivia.obtener_trivia_activa()
        if token_publico:
            sesion = (
                SesionProceso.objects.select_for_update()
                .select_related("trivia")
                .filter(token_publico=token_publico)
                .first()
            )
            if sesion:
                sesion.user_agent = ServicioSesiones._extraer_user_agent(request)
                if not sesion.ip_origen:
                    sesion.ip_origen = ServicioSesiones._extraer_ip(request)
                sesion.fecha_actualizacion = timezone.now()
                sesion.save(
                    update_fields=[
                        "user_agent",
                        "ip_origen",
                        "fecha_actualizacion",
                        "actualizado_en",
                    ]
                )
                return sesion, False

        sesion = SesionProceso.objects.create(
            trivia=trivia,
            ip_origen=ServicioSesiones._extraer_ip(request),
            user_agent=ServicioSesiones._extraer_user_agent(request),
        )
        return sesion, True

    @staticmethod
    def obtener_sesion_por_token(*, token_publico) -> SesionProceso:
        try:
            return SesionProceso.objects.select_related("trivia").get(
                token_publico=token_publico
            )
        except SesionProceso.DoesNotExist as exc:
            raise ErrorDeDominio(
                "No se encontro la sesion solicitada.",
                codigo="sesion_no_encontrada",
                estado_http=404,
            ) from exc

    @staticmethod
    def validar_carga_habilitada(sesion: SesionProceso):
        if not isinstance(sesion, SesionProceso):
            sesion = ServicioSesiones.obtener_sesion_por_token(token_publico=sesion)
        else:
            sesion = SesionProceso.objects.get(id=sesion.id)
        if not sesion.trivia_completada or not sesion.puede_subir_foto:
            raise ErrorDeDominio(
                "Debes completar todas las preguntas obligatorias antes de subir una foto.",
                codigo="trivia_incompleta",
                estado_http=409,
            )

    @staticmethod
    def validar_foto_pertenece_a_sesion(*, sesion: SesionProceso, foto):
        if foto.sesion_id != sesion.id:
            raise ErrorDeDominio(
                "La foto indicada no pertenece a la sesion enviada.",
                codigo="foto_fuera_de_sesion",
                estado_http=403,
            )

    @staticmethod
    def validar_recorte_pertenece_a_sesion(*, sesion: SesionProceso, resultado_recorte):
        if resultado_recorte.foto_original.sesion_id != sesion.id:
            raise ErrorDeDominio(
                "El recorte indicado no pertenece a la sesion enviada.",
                codigo="recorte_fuera_de_sesion",
                estado_http=403,
            )

    @staticmethod
    @transaction.atomic
    def actualizar_estado_cuestionario(*, sesion: SesionProceso, es_completa: bool):
        sesion = SesionProceso.objects.select_for_update().get(id=sesion.id)
        sesion.trivia_completada = es_completa
        sesion.puede_subir_foto = es_completa
        sesion.fecha_actualizacion = timezone.now()
        sesion.save(
            update_fields=[
                "trivia_completada",
                "puede_subir_foto",
                "fecha_actualizacion",
                "actualizado_en",
            ]
        )
        return sesion

    @staticmethod
    @transaction.atomic
    def sincronizar_estado_proceso(*, sesion: SesionProceso):
        sesion = SesionProceso.objects.select_for_update().get(id=sesion.id)
        ultima_foto = sesion.fotos.order_by("-fecha_subida").first()
        ultima_figurita = sesion.figuritas.order_by("-creado_en").first()

        nuevo_estado = EstadoProceso.PENDIENTE
        fecha_fin = None
        if ultima_figurita:
            if ultima_figurita.estado == EstadoProceso.COMPLETADO:
                nuevo_estado = EstadoProceso.COMPLETADO
                fecha_fin = ultima_figurita.fecha_generacion or timezone.now()
            elif ultima_figurita.estado == EstadoProceso.PROCESANDO:
                nuevo_estado = EstadoProceso.PROCESANDO
            elif ultima_figurita.estado == EstadoProceso.ERROR:
                nuevo_estado = EstadoProceso.ERROR
        elif ultima_foto:
            if ultima_foto.estado == EstadoProceso.PROCESANDO:
                nuevo_estado = EstadoProceso.PROCESANDO
            elif ultima_foto.estado == EstadoProceso.ERROR:
                nuevo_estado = EstadoProceso.ERROR

        sesion.estado = nuevo_estado
        sesion.fecha_fin = fecha_fin
        sesion.fecha_actualizacion = timezone.now()
        sesion.save(
            update_fields=["estado", "fecha_fin", "fecha_actualizacion", "actualizado_en"]
        )
        return sesion

    @staticmethod
    def obtener_estado_serializado(sesion: SesionProceso) -> dict:
        from trivias.api.serializers import DatosStickerSerializer
        from trivias.services.servicio_validacion_sticker import ServicioValidacionSticker

        sesion = ServicioSesiones.sincronizar_estado_proceso(sesion=sesion)
        respuestas = sesion.respuestas.select_related("pregunta")
        preguntas = sesion.trivia.preguntas.filter(activa=True)
        evaluacion = ServicioValidacionSticker.evaluar_sesion(sesion)
        datos_sticker = getattr(sesion, "datos_sticker", None)
        ultima_foto = sesion.fotos.order_by("-fecha_subida").first()
        ultimo_recorte = None
        if ultima_foto and hasattr(ultima_foto, "resultado_recorte"):
            ultimo_recorte = ultima_foto.resultado_recorte
        ultima_figurita = sesion.figuritas.order_by("-creado_en").first()

        return {
            "id": sesion.id,
            "token_publico": sesion.token_publico,
            "estado": sesion.estado,
            "trivia_id": sesion.trivia_id,
            "trivia_completada": sesion.trivia_completada,
            "puede_subir_foto": sesion.puede_subir_foto,
            "fecha_inicio": sesion.fecha_inicio,
            "fecha_actualizacion": sesion.fecha_actualizacion,
            "progreso": {
                "preguntas_totales": preguntas.count(),
                "preguntas_respondidas": respuestas.count(),
                "campos_obligatorios_totales": len(evaluacion["campos_requeridos"]),
                "campos_obligatorios_completos": len(evaluacion["campos_completos"]),
                "porcentaje": evaluacion["porcentaje"],
                "campos_faltantes": evaluacion["campos_faltantes"],
            },
            "datos_sticker": DatosStickerSerializer(datos_sticker).data if datos_sticker else None,
            "ultima_foto": {
                "id": ultima_foto.id,
                "estado": ultima_foto.estado,
                "nombre_original": ultima_foto.nombre_original,
            }
            if ultima_foto
            else None,
            "ultimo_recorte": {
                "id": ultimo_recorte.id,
                "estado": ultimo_recorte.estado,
                "modelo_gemini": ultimo_recorte.modelo_gemini,
            }
            if ultimo_recorte
            else None,
            "ultima_figurita": {
                "id": ultima_figurita.id,
                "estado": ultima_figurita.estado,
                "nombre_mostrado": ultima_figurita.nombre_mostrado,
            }
            if ultima_figurita
            else None,
        }
