from django.urls import path

from figuritas.api.views import VistaGenerarFiguritaSesionAPIView
from imagenes.api.views import VistaSubirImagenAPIView
from sesiones.api.views import (
    VistaEstadoSesionAPIView,
    VistaIniciarSesionAPIView,
    VistaPreguntasSesionAPIView,
    VistaResponderSesionAPIView,
)

urlpatterns = [
    path("iniciar/", VistaIniciarSesionAPIView.as_view(), name="sesion-iniciar"),
    path(
        "<uuid:token_publico>/preguntas/",
        VistaPreguntasSesionAPIView.as_view(),
        name="sesion-preguntas",
    ),
    path(
        "<uuid:token_publico>/responder/",
        VistaResponderSesionAPIView.as_view(),
        name="sesion-responder",
    ),
    path(
        "<uuid:token_publico>/estado/",
        VistaEstadoSesionAPIView.as_view(),
        name="sesion-estado",
    ),
    path(
        "<uuid:token_publico>/imagenes/subir/",
        VistaSubirImagenAPIView.as_view(),
        name="sesion-imagen-subir",
    ),
    path(
        "<uuid:token_publico>/figuritas/generar/",
        VistaGenerarFiguritaSesionAPIView.as_view(),
        name="sesion-figurita-generar",
    ),
]
