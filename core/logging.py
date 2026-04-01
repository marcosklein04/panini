def obtener_configuracion_logging(debug: bool) -> dict:
    nivel = "DEBUG" if debug else "INFO"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            }
        },
        "root": {"handlers": ["console"], "level": nivel},
        "loggers": {
            "django": {"handlers": ["console"], "level": nivel, "propagate": False},
            "celery": {"handlers": ["console"], "level": nivel, "propagate": False},
        },
    }
