from django.urls import path

from figuritas.api.views import VistaDetalleFiguritaAPIView

urlpatterns = [
    path("<uuid:figurita_id>/", VistaDetalleFiguritaAPIView.as_view(), name="figurita-detalle"),
]
