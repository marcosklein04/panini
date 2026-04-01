from django.urls import path

from catalogos.api.views import VistaEquiposAPIView

urlpatterns = [
    path("equipos/", VistaEquiposAPIView.as_view(), name="catalogo-equipos"),
]
