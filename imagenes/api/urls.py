from django.urls import path

from imagenes.api.views import VistaProcesarImagenAPIView, VistaResultadoImagenAPIView

urlpatterns = [
    path(
        "<uuid:foto_id>/procesar/",
        VistaProcesarImagenAPIView.as_view(),
        name="imagen-procesar",
    ),
    path("<uuid:foto_id>/resultado/", VistaResultadoImagenAPIView.as_view(), name="imagen-resultado"),
]
