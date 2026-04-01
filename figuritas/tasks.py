from celery import shared_task

from core.excepciones import ErrorDeDominio
from figuritas.services.servicio_composicion_figurita import ServicioComposicionFigurita


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def tarea_generar_figurita(self, figurita_id: str):
    try:
        return str(
            ServicioComposicionFigurita.generar_figurita(
                figurita_id=figurita_id,
                task_id=self.request.id,
            ).id
        )
    except ErrorDeDominio as exc:
        ServicioComposicionFigurita.marcar_error(
            figurita_id=figurita_id, mensaje=exc.mensaje
        )
        raise
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        ServicioComposicionFigurita.marcar_error(
            figurita_id=figurita_id,
            mensaje="No fue posible generar la figurita.",
        )
        raise
