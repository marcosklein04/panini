from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView

from core.salud import VistaHealthCheck
from core.views import VistaInicioFrontend

urlpatterns = [
    path("", VistaInicioFrontend.as_view(), name="inicio"),
    path("prueba/", RedirectView.as_view(pattern_name="inicio", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/health/", VistaHealthCheck.as_view(), name="health"),
    path("api/catalogos/", include("catalogos.api.urls")),
    path("api/trivias/", include("trivias.api.urls")),
    path("api/sesiones/", include("sesiones.api.urls")),
    path("api/imagenes/", include("imagenes.api.urls")),
    path("api/figuritas/", include("figuritas.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()
