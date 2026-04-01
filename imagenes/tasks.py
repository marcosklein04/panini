from celery import shared_task

from core.excepciones import ErrorDeDominio
from imagenes.services.servicio_recorte_imagen import ServicioRecorteImagen


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def tarea_procesar_imagen(self, foto_id: str, plantilla_id: str | None = None):
    try:
        return str(
            ServicioRecorteImagen.procesar_foto(
                foto_id=foto_id,
                plantilla_id=plantilla_id,
                task_id=self.request.id,
            ).id
        )
    except ErrorDeDominio as exc:
        ServicioRecorteImagen.marcar_error(foto_id=foto_id, mensaje=exc.mensaje)
        raise
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        ServicioRecorteImagen.marcar_error(
            foto_id=foto_id,
            mensaje="No fue posible completar el recorte de la imagen.",
        )
        raise
