from __future__ import annotations

from collections import Counter

from django.db import transaction
from django.db.models import Prefetch

from catalogos.models import Equipo
from core.enums import TipoRespuestaTrivia
from core.excepciones import ErrorDeDominio
from trivias.models import DatosSticker, OpcionRespuesta, PreguntaTrivia, RespuestaTrivia, Trivia
from trivias.services.servicio_validacion_sticker import ServicioValidacionSticker


class ServicioTrivia:
    @staticmethod
    def obtener_trivia_activa() -> Trivia:
        trivia = (
            Trivia.objects.filter(activa=True)
            .prefetch_related(
                Prefetch(
                    "preguntas",
                    queryset=PreguntaTrivia.objects.filter(activa=True).prefetch_related(
                        Prefetch(
                            "opciones",
                            queryset=OpcionRespuesta.objects.filter(activa=True).order_by(
                                "orden", "creado_en"
                            ),
                        )
                    ),
                )
            )
            .order_by("-creado_en")
            .first()
        )
        if not trivia:
            raise ErrorDeDominio(
                "No hay una trivia activa disponible.",
                codigo="trivia_no_disponible",
                estado_http=404,
            )
        return trivia

    @staticmethod
    def obtener_preguntas_sesion(sesion) -> list[PreguntaTrivia]:
        return list(
            sesion.trivia.preguntas.filter(activa=True).prefetch_related(
                Prefetch(
                    "opciones",
                    queryset=OpcionRespuesta.objects.filter(activa=True).order_by(
                        "orden", "creado_en"
                    ),
                )
            )
        )

    @staticmethod
    def obtener_o_crear_datos_sticker(sesion):
        datos_sticker, _ = DatosSticker.objects.get_or_create(sesion=sesion)
        return datos_sticker

    @staticmethod
    @transaction.atomic
    def responder_sesion(*, sesion, payload: dict):
        preguntas = {
            str(pregunta.id): pregunta
            for pregunta in ServicioTrivia.obtener_preguntas_sesion(sesion)
        }
        respuestas_entrada = payload.get("respuestas")
        if not respuestas_entrada:
            respuestas_entrada = [
                {
                    "pregunta_id": payload["pregunta_id"],
                    "valor": payload.get("valor"),
                    "opcion_id": payload.get("opcion_id"),
                    "equipo_id": payload.get("equipo_id"),
                }
            ]

        ids_recibidos = [str(item["pregunta_id"]) for item in respuestas_entrada]
        conteo = Counter(ids_recibidos)
        duplicadas = [pregunta_id for pregunta_id, total in conteo.items() if total > 1]
        if duplicadas:
            raise ErrorDeDominio(
                "No puedes responder la misma pregunta mas de una vez en el mismo envio.",
                codigo="preguntas_duplicadas",
                campos={"preguntas": duplicadas},
            )

        datos_sticker = ServicioTrivia.obtener_o_crear_datos_sticker(sesion)
        respuestas_guardadas = []
        for item in respuestas_entrada:
            pregunta = preguntas.get(str(item["pregunta_id"]))
            if not pregunta:
                raise ErrorDeDominio(
                    "Una de las preguntas enviadas no pertenece al flujo actual.",
                    codigo="pregunta_invalida",
                    campos={"pregunta_id": str(item["pregunta_id"])},
                )

            opcion = None
            equipo = None
            if pregunta.tipo_respuesta == TipoRespuestaTrivia.OPCION_UNICA:
                opcion_id = item.get("opcion_id")
                if not opcion_id:
                    raise ErrorDeDominio(
                        "Debes indicar la opcion elegida.",
                        codigo="opcion_requerida",
                        campos={"pregunta_id": str(pregunta.id)},
                    )
                opcion = pregunta.opciones.filter(id=opcion_id, activa=True).first()
                if not opcion:
                    raise ErrorDeDominio(
                        "La opcion enviada no existe o no esta activa.",
                        codigo="opcion_invalida",
                        campos={
                            "pregunta_id": str(pregunta.id),
                            "opcion_id": str(opcion_id),
                        },
                    )
            elif pregunta.tipo_respuesta == TipoRespuestaTrivia.SELECT_BUSQUEDA:
                equipo_id = item.get("equipo_id")
                if not equipo_id:
                    raise ErrorDeDominio(
                        "Debes indicar el equipo seleccionado.",
                        codigo="equipo_requerido",
                        campos={"pregunta_id": str(pregunta.id)},
                    )
                equipo = Equipo.objects.filter(id=equipo_id, activa=True).first()
                if not equipo:
                    raise ErrorDeDominio(
                        "El equipo seleccionado no existe o no esta activo.",
                        codigo="equipo_invalido",
                        campos={
                            "pregunta_id": str(pregunta.id),
                            "equipo_id": str(equipo_id),
                        },
                    )

            validacion = ServicioValidacionSticker.validar_respuesta(
                pregunta=pregunta,
                payload=item,
                opcion=opcion,
                equipo=equipo,
            )
            defaults = {
                "valor_texto": validacion["campos_respuesta"]["valor_texto"],
                "valor_numero": validacion["campos_respuesta"]["valor_numero"],
                "valor_fecha": validacion["campos_respuesta"]["valor_fecha"],
                "valor_opcion": validacion["campos_respuesta"]["valor_opcion"],
                "valor_equipo": validacion["campos_respuesta"]["valor_equipo"],
            }
            respuesta, _ = RespuestaTrivia.objects.update_or_create(
                sesion=sesion,
                pregunta=pregunta,
                defaults=defaults,
            )
            respuestas_guardadas.append(respuesta)

            for campo, valor in validacion["campos_sticker"].items():
                setattr(datos_sticker, campo, valor)

        datos_sticker.save()

        from sesiones.services.servicio_sesiones import ServicioSesiones

        evaluacion = ServicioValidacionSticker.evaluar_sesion(sesion)
        sesion = ServicioSesiones.actualizar_estado_cuestionario(
            sesion=sesion,
            es_completa=evaluacion["es_completa"],
        )
        return sesion, datos_sticker, respuestas_guardadas, evaluacion
