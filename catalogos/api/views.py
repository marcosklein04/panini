from rest_framework.generics import ListAPIView

from catalogos.api.serializers import EquipoSerializer
from catalogos.models import Equipo
from core.throttling import ThrottleCatalogosEquipos


class VistaEquiposAPIView(ListAPIView):
    serializer_class = EquipoSerializer
    throttle_classes = [ThrottleCatalogosEquipos]

    def get_queryset(self):
        consulta = Equipo.objects.filter(activa=True)
        termino = self.request.query_params.get("q", "").strip()
        if termino:
            consulta = consulta.filter(nombre__icontains=termino)
        return consulta.order_by("orden", "nombre")[:20]
