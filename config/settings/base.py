from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from core.logging import obtener_configuracion_logging

BASE_DIR = Path(__file__).resolve().parents[2]


def cargar_archivo_entorno() -> None:
    ruta_entorno = BASE_DIR / ".env"
    if not ruta_entorno.exists():
        return

    for linea in ruta_entorno.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")
        os.environ[clave] = valor


def leer_entorno(nombre: str, default: str | None = None, requerido: bool = False) -> str:
    valor = os.getenv(nombre, default)
    if requerido and (valor is None or valor == ""):
        raise ImproperlyConfigured(f"La variable de entorno {nombre} es obligatoria.")
    if valor is None:
        raise ImproperlyConfigured(f"La variable de entorno {nombre} es obligatoria.")
    return valor


def leer_bool(nombre: str, default: bool = False) -> bool:
    valor = os.getenv(nombre)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "t", "si", "yes", "y"}


def leer_int(nombre: str, default: int) -> int:
    valor = os.getenv(nombre)
    if valor is None or valor == "":
        return default
    try:
        return int(valor)
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"La variable de entorno {nombre} debe ser un numero entero."
        ) from exc


def leer_lista(nombre: str, default: list[str] | None = None) -> list[str]:
    valor = os.getenv(nombre)
    if valor is None or valor.strip() == "":
        return default or []
    return [item.strip() for item in valor.split(",") if item.strip()]


cargar_archivo_entorno()

SECRET_KEY = leer_entorno("SECRET_KEY", requerido=True)
DEBUG = leer_bool("DEBUG", default=False)
ALLOWED_HOSTS = leer_lista("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
if DEBUG and ALLOWED_HOSTS == ["localhost", "127.0.0.1"]:
    ALLOWED_HOSTS = ["*"]
CELERY_TASK_ALWAYS_EAGER = leer_bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = leer_bool(
    "CELERY_TASK_EAGER_PROPAGATES", default=CELERY_TASK_ALWAYS_EAGER
)

POSTGRES_DB = leer_entorno("POSTGRES_DB", requerido=True)
POSTGRES_USER = leer_entorno("POSTGRES_USER", requerido=True)
POSTGRES_PASSWORD = leer_entorno("POSTGRES_PASSWORD", requerido=True)
POSTGRES_HOST = leer_entorno("POSTGRES_HOST", requerido=True)
POSTGRES_PORT = leer_entorno("POSTGRES_PORT", default="5432", requerido=True)

REDIS_URL = leer_entorno(
    "REDIS_URL",
    default="redis://localhost:6379/0" if CELERY_TASK_ALWAYS_EAGER else None,
    requerido=not CELERY_TASK_ALWAYS_EAGER,
)
GEMINI_API_KEY = leer_entorno("GEMINI_API_KEY", default="")
GEMINI_MODEL = leer_entorno("GEMINI_MODEL", default="gemini-2.5-flash")
GEMINI_MODO_SIMULADO = leer_bool("GEMINI_MODO_SIMULADO", default=DEBUG)
GEMINI_FALLBACK_LOCAL = leer_bool("GEMINI_FALLBACK_LOCAL", default=DEBUG)
GEMINI_TIMEOUT_SEGUNDOS = leer_int("GEMINI_TIMEOUT_SEGUNDOS", default=20)
CORS_ALLOWED_ORIGINS = leer_lista("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_ALL_ORIGINS = leer_bool("CORS_ALLOW_ALL_ORIGINS", default=DEBUG)
MEDIA_ROOT = Path(leer_entorno("MEDIA_ROOT", default=str(BASE_DIR / "media")))
MEDIA_URL = leer_entorno("MEDIA_URL", default="/media/")
JWT_ACCESS_MINUTOS = leer_int("JWT_ACCESS_MINUTOS", default=60)
JWT_REFRESH_DIAS = leer_int("JWT_REFRESH_DIAS", default=7)
MAX_TAMANO_IMAGEN_MB = leer_int("MAX_TAMANO_IMAGEN_MB", default=10)
MIN_ANCHO_IMAGEN = leer_int("MIN_ANCHO_IMAGEN", default=400)
MIN_ALTO_IMAGEN = leer_int("MIN_ALTO_IMAGEN", default=400)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "usuarios.apps.UsuariosConfig",
    "catalogos.apps.CatalogosConfig",
    "trivias.apps.TriviasConfig",
    "sesiones.apps.SesionesConfig",
    "imagenes.apps.ImagenesConfig",
    "figuritas.apps.FiguritasConfig",
    "core.apps.CoreConfig",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": POSTGRES_DB,
        "USER": POSTGRES_USER,
        "PASSWORD": POSTGRES_PASSWORD,
        "HOST": POSTGRES_HOST,
        "PORT": POSTGRES_PORT,
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"connect_timeout": 5},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": str(MEDIA_ROOT), "base_url": MEDIA_URL},
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "usuarios.Usuario"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "EXCEPTION_HANDLER": "core.manejador_excepciones.manejador_excepciones_es",
    "DEFAULT_THROTTLE_RATES": {
        "sesiones_iniciar": "30/hour",
        "sesiones_responder": "300/hour",
        "catalogos_equipos": "120/minute",
        "imagenes_subir": "20/hour",
        "imagenes_procesar": "30/hour",
        "figuritas_generar": "30/hour",
    },
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=JWT_ACCESS_MINUTOS),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=JWT_REFRESH_DIAS),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
if CELERY_TASK_ALWAYS_EAGER and not REDIS_URL:
    CELERY_BROKER_URL = "memory://"
    CELERY_RESULT_BACKEND = "cache+memory://"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 15 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 10 * 60
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = CELERY_TASK_ALWAYS_EAGER
CELERY_TASK_EAGER_PROPAGATES = CELERY_TASK_EAGER_PROPAGATES

LOGGING = obtener_configuracion_logging(DEBUG)
