from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from core.enums import CampoSticker, TipoRespuestaTrivia
from core.excepciones import ErrorDeDominio


class ServicioValidacionSticker:
    REGLAS_POR_CODIGO = {
        "nombre": {"requerido": True, "max_length": 100},
        "apellido": {"requerido": True, "max_length": 100},
        "fecha_nacimiento": {"requerido": True, "edad_minima": 5, "edad_maxima": 100},
        "altura_cm": {"requerido": True, "min": 80, "max": 250},
        "peso_kg": {"requerido": True, "min": 20, "max": 250},
        "equipo": {"requerido": True},
        "apodo": {"requerido": False, "max_length": 100},
        "posicion": {"requerido": False, "max_length": 100},
        "nacionalidad": {"requerido": False, "max_length": 100},
    }
    CAMPOS_REQUERIDOS = [
        CampoSticker.NOMBRE,
        CampoSticker.APELLIDO,
        CampoSticker.FECHA_NACIMIENTO,
        CampoSticker.ALTURA_CM,
        CampoSticker.PESO_KG,
        CampoSticker.EQUIPO,
    ]

    @classmethod
    def obtener_reglas(cls, pregunta) -> dict:
        reglas = dict(cls.REGLAS_POR_CODIGO.get(pregunta.codigo, {}))
        reglas.update(pregunta.reglas_validacion or {})
        return reglas

    @classmethod
    def validar_respuesta(cls, *, pregunta, payload: dict, opcion=None, equipo=None) -> dict:
        reglas = cls.obtener_reglas(pregunta)
        tipo = pregunta.tipo_respuesta
        campo = pregunta.mapea_a_campo_sticker

        if tipo == TipoRespuestaTrivia.TEXTO:
            valor = str(payload.get("valor") or "").strip()
            if reglas.get("requerido") and not valor:
                raise ErrorDeDominio(
                    "Debes completar este campo.",
                    codigo="respuesta_requerida",
                    campos={"pregunta_id": str(pregunta.id)},
                )
            max_length = reglas.get("max_length")
            if max_length and len(valor) > int(max_length):
                raise ErrorDeDominio(
                    "El texto supera la longitud maxima permitida.",
                    codigo="texto_demasiado_largo",
                    campos={"max_length": int(max_length), "pregunta_id": str(pregunta.id)},
                )
            return {
                "campos_respuesta": {
                    "valor_texto": valor,
                    "valor_numero": None,
                    "valor_fecha": None,
                    "valor_opcion": None,
                    "valor_equipo": None,
                },
                "campos_sticker": {campo: valor},
            }

        if tipo == TipoRespuestaTrivia.FECHA:
            valor = payload.get("valor")
            if not valor:
                raise ErrorDeDominio(
                    "Debes enviar una fecha valida.",
                    codigo="fecha_requerida",
                    campos={"pregunta_id": str(pregunta.id)},
                )
            if isinstance(valor, str):
                try:
                    fecha = date.fromisoformat(valor)
                except ValueError as exc:
                    raise ErrorDeDominio(
                        "La fecha enviada no es valida.",
                        codigo="fecha_invalida",
                        campos={"pregunta_id": str(pregunta.id)},
                    ) from exc
            elif isinstance(valor, date):
                fecha = valor
            else:
                raise ErrorDeDominio(
                    "La fecha enviada no es valida.",
                    codigo="fecha_invalida",
                    campos={"pregunta_id": str(pregunta.id)},
                )
            edad = cls._calcular_edad(fecha)
            if edad < int(reglas.get("edad_minima", 0)) or edad > int(
                reglas.get("edad_maxima", 200)
            ):
                raise ErrorDeDominio(
                    "La fecha de nacimiento queda fuera del rango permitido.",
                    codigo="edad_fuera_de_rango",
                    campos={"pregunta_id": str(pregunta.id), "edad": edad},
                )
            return {
                "campos_respuesta": {
                    "valor_texto": "",
                    "valor_numero": None,
                    "valor_fecha": fecha,
                    "valor_opcion": None,
                    "valor_equipo": None,
                },
                "campos_sticker": {campo: fecha},
            }

        if tipo == TipoRespuestaTrivia.NUMERO:
            valor = payload.get("valor")
            try:
                numero = Decimal(str(valor))
            except (InvalidOperation, TypeError) as exc:
                raise ErrorDeDominio(
                    "Debes enviar un numero valido.",
                    codigo="numero_invalido",
                    campos={"pregunta_id": str(pregunta.id)},
                ) from exc
            if numero != numero.quantize(Decimal("1")):
                raise ErrorDeDominio(
                    "Este campo solo admite numeros enteros.",
                    codigo="numero_entero_requerido",
                    campos={"pregunta_id": str(pregunta.id)},
                )
            entero = int(numero)
            if entero < int(reglas.get("min", -10000)) or entero > int(
                reglas.get("max", 10000)
            ):
                raise ErrorDeDominio(
                    "El valor numerico queda fuera del rango permitido.",
                    codigo="numero_fuera_de_rango",
                    campos={"pregunta_id": str(pregunta.id), "valor": entero},
                )
            return {
                "campos_respuesta": {
                    "valor_texto": "",
                    "valor_numero": Decimal(entero),
                    "valor_fecha": None,
                    "valor_opcion": None,
                    "valor_equipo": None,
                },
                "campos_sticker": {campo: entero},
            }

        if tipo == TipoRespuestaTrivia.OPCION_UNICA:
            if not opcion:
                raise ErrorDeDominio(
                    "Debes seleccionar una opcion valida.",
                    codigo="opcion_requerida",
                    campos={"pregunta_id": str(pregunta.id)},
                )
            return {
                "campos_respuesta": {
                    "valor_texto": opcion.etiqueta,
                    "valor_numero": None,
                    "valor_fecha": None,
                    "valor_opcion": opcion,
                    "valor_equipo": None,
                },
                "campos_sticker": {campo: opcion.etiqueta},
            }

        if tipo == TipoRespuestaTrivia.SELECT_BUSQUEDA:
            if not equipo:
                raise ErrorDeDominio(
                    "Debes seleccionar un equipo valido.",
                    codigo="equipo_requerido",
                    campos={"pregunta_id": str(pregunta.id)},
                )
            return {
                "campos_respuesta": {
                    "valor_texto": equipo.nombre,
                    "valor_numero": None,
                    "valor_fecha": None,
                    "valor_opcion": None,
                    "valor_equipo": equipo,
                },
                "campos_sticker": {
                    campo: equipo.nombre,
                    "equipo_catalogo": equipo,
                },
            }

        raise ErrorDeDominio(
            "La pregunta tiene un tipo de respuesta no soportado.",
            codigo="tipo_respuesta_no_soportado",
            estado_http=500,
        )

    @classmethod
    def evaluar_sesion(cls, sesion) -> dict:
        datos = getattr(sesion, "datos_sticker", None)
        campos_completos = []
        campos_faltantes = []
        if datos:
            for campo in cls.CAMPOS_REQUERIDOS:
                valor = getattr(datos, campo, None)
                completo = bool(valor) if campo == CampoSticker.EQUIPO else valor not in (None, "")
                if completo:
                    campos_completos.append(campo)
                else:
                    campos_faltantes.append(campo)
        else:
            campos_faltantes = list(cls.CAMPOS_REQUERIDOS)

        porcentaje = int((len(campos_completos) / len(cls.CAMPOS_REQUERIDOS)) * 100)
        return {
            "campos_requeridos": [campo for campo in cls.CAMPOS_REQUERIDOS],
            "campos_completos": [campo for campo in campos_completos],
            "campos_faltantes": [campo for campo in campos_faltantes],
            "es_completa": not campos_faltantes,
            "porcentaje": porcentaje,
        }

    @staticmethod
    def _calcular_edad(fecha_nacimiento: date) -> int:
        hoy = timezone.localdate()
        return hoy.year - fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day)
        )
