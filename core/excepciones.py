class ErrorDeDominio(Exception):
    def __init__(
        self,
        mensaje: str,
        *,
        codigo: str = "error_de_dominio",
        estado_http: int = 400,
        campos: dict | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
        self.estado_http = estado_http
        self.campos = campos or {}
