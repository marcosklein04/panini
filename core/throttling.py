from rest_framework.throttling import SimpleRateThrottle


class ThrottleIdentidadPublica(SimpleRateThrottle):
    scope = "generico"

    def get_cache_key(self, request, view):
        identificador = self._obtener_identificador(request)
        return self.cache_format % {"scope": self.scope, "ident": identificador}

    def _obtener_identificador(self, request):
        token_publico = None
        if getattr(request, "resolver_match", None):
            token_publico = request.resolver_match.kwargs.get("token_publico")
        if not token_publico:
            token_publico = request.query_params.get("token_publico")
        if not token_publico and hasattr(request, "data"):
            try:
                token_publico = request.data.get("token_publico")
            except Exception:
                token_publico = None
        return str(token_publico or self.get_ident(request))


class ThrottleSesionIniciar(ThrottleIdentidadPublica):
    scope = "sesiones_iniciar"


class ThrottleSesionResponder(ThrottleIdentidadPublica):
    scope = "sesiones_responder"


class ThrottleCatalogosEquipos(ThrottleIdentidadPublica):
    scope = "catalogos_equipos"


class ThrottleSubidaImagen(ThrottleIdentidadPublica):
    scope = "imagenes_subir"


class ThrottleProcesamientoImagen(ThrottleIdentidadPublica):
    scope = "imagenes_procesar"


class ThrottleGeneracionFigurita(ThrottleIdentidadPublica):
    scope = "figuritas_generar"
