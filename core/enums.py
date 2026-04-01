from django.db import models


class EstadoProceso(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    PROCESANDO = "procesando", "Procesando"
    COMPLETADO = "completado", "Completado"
    ERROR = "error", "Error"


class TipoRespuestaTrivia(models.TextChoices):
    TEXTO = "texto", "Texto"
    FECHA = "fecha", "Fecha"
    NUMERO = "numero", "Numero"
    OPCION_UNICA = "opcion_unica", "Opcion unica"
    SELECT_BUSQUEDA = "select_busqueda", "Select con busqueda"


class CampoSticker(models.TextChoices):
    NOMBRE = "nombre", "Nombre"
    APELLIDO = "apellido", "Apellido"
    FECHA_NACIMIENTO = "fecha_nacimiento", "Fecha de nacimiento"
    ALTURA_CM = "altura_cm", "Altura en cm"
    PESO_KG = "peso_kg", "Peso en kg"
    EQUIPO = "equipo", "Equipo"
    APODO = "apodo", "Apodo"
    POSICION = "posicion", "Posicion"
    NACIONALIDAD = "nacionalidad", "Nacionalidad"


class ProveedorIA(models.TextChoices):
    GEMINI = "gemini", "Gemini"
