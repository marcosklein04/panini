from django.urls import path

from usuarios.api.views import VistaLoginAPIView, VistaRegistroAPIView

urlpatterns = [
    path("registro/", VistaRegistroAPIView.as_view(), name="registro"),
    path("login/", VistaLoginAPIView.as_view(), name="login"),
]
