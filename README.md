# Panini Backend

Backend en Django + Django REST Framework para un flujo anonimo de cuestionario guiado + carga de foto + recorte con Gemini + generacion de figurita estilo deportiva.

## Arquitectura breve

- `usuarios`: modelo custom de usuario para admin y evolucion futura, fuera del flujo publico.
- `catalogos`: catalogos administrables, hoy usados para equipos.
- `trivias`: definicion del cuestionario, preguntas por paso, respuestas y `DatosSticker` normalizados.
- `sesiones`: sesion anonima reanudable por `token_publico`.
- `imagenes`: subida segura, validacion de archivos, Gemini, mascara y recorte PNG.
- `figuritas`: plantillas configurables y composicion final de la figurita.
- `core`: configuracion compartida, errores uniformes, healthcheck, logging y frontend de prueba.

## Arbol principal

```text
config/
core/
usuarios/
catalogos/
trivias/
sesiones/
imagenes/
figuritas/
tests/
docker/
manage.py
requirements.txt
Dockerfile
docker-compose.yml
.env.example
```

## Flujo principal

1. El frontend llama `POST /api/sesiones/iniciar/`.
2. El backend crea o reanuda una `SesionProceso` anonima y devuelve `token_publico`.
3. El frontend obtiene la trivia activa y las preguntas ordenadas.
4. El usuario responde las preguntas requeridas.
5. El backend normaliza las respuestas en `DatosSticker`.
6. Cuando los campos obligatorios quedan completos y validos, se habilita la subida de foto.
7. El usuario sube la imagen original.
8. El backend usa Gemini para guiar la segmentacion y luego aplica refinado local.
9. Se genera el PNG transparente y, si hay plantilla predeterminada, se encola una figurita base.
10. El frontend consulta estado, resultado de imagen y figurita final.

## Variables de entorno

Usa `.env.example` como base.

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `REDIS_URL`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_MODO_SIMULADO`
- `MEDIA_ROOT`
- `MEDIA_URL`
- `CORS_ALLOWED_ORIGINS`
- `MAX_TAMANO_IMAGEN_MB`
- `MIN_ANCHO_IMAGEN`
- `MIN_ALTO_IMAGEN`
- `CELERY_TASK_ALWAYS_EAGER`
- `CELERY_TASK_EAGER_PROPAGATES`

## Puesta en marcha local

1. Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

2. Crear `.env`:

```powershell
Copy-Item .env.example .env -Force
```

3. Completar credenciales reales de PostgreSQL y, si corresponde, de Gemini.

4. Ejecutar migraciones:

```bash
py manage.py makemigrations usuarios catalogos trivias sesiones imagenes figuritas
py manage.py migrate
```

5. Cargar datos demo:

```bash
py manage.py cargar_datos_demo
```

6. Levantar la API:

```bash
py manage.py run
```

7. Abrir el panel basico de prueba:

```text
http://localhost:8000/
```

## Desarrollo con Celery

En desarrollo puedes dejar:

```env
CELERY_TASK_ALWAYS_EAGER=True
CELERY_TASK_EAGER_PROPAGATES=True
```

Con eso el procesamiento se ejecuta en la misma request y no necesitas worker ni Redis para probar el flujo.

Si quieres correr worker real:

```bash
celery -A config worker --loglevel=info
```

## Docker

```bash
docker compose up -d --build
docker compose exec api python manage.py migrate
docker compose exec api python manage.py cargar_datos_demo
```

## API publica

- `POST /api/sesiones/iniciar/`
- `GET /api/trivias/activa/`
- `GET /api/sesiones/{token_publico}/preguntas/`
- `POST /api/sesiones/{token_publico}/responder/`
- `GET /api/sesiones/{token_publico}/estado/`
- `GET /api/catalogos/equipos/?q=...`
- `POST /api/sesiones/{token_publico}/imagenes/subir/`
- `POST /api/imagenes/{id}/procesar/`
- `GET /api/imagenes/{id}/resultado/`
- `POST /api/sesiones/{token_publico}/figuritas/generar/`
- `GET /api/figuritas/{id}/`
- `GET /api/health/`

## Ejemplos de requests

### Iniciar o reanudar sesion

```bash
curl -X POST http://localhost:8000/api/sesiones/iniciar/ \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Obtener trivia activa

```bash
curl http://localhost:8000/api/trivias/activa/
```

### Obtener preguntas de la sesion

```bash
curl http://localhost:8000/api/sesiones/TOKEN_PUBLICO/preguntas/
```

### Responder el cuestionario

```bash
curl -X POST http://localhost:8000/api/sesiones/TOKEN_PUBLICO/responder/ \
  -H "Content-Type: application/json" \
  -d '{
    "respuestas": [
      {"pregunta_id": "UUID_NOMBRE", "valor": "Lionel"},
      {"pregunta_id": "UUID_APELLIDO", "valor": "Messi"},
      {"pregunta_id": "UUID_FECHA", "valor": "1987-06-24"},
      {"pregunta_id": "UUID_ALTURA", "valor": 170},
      {"pregunta_id": "UUID_PESO", "valor": 72},
      {"pregunta_id": "UUID_EQUIPO", "equipo_id": "UUID_EQUIPO"}
    ]
  }'
```

### Subir imagen

```bash
curl -X POST http://localhost:8000/api/sesiones/TOKEN_PUBLICO/imagenes/subir/ \
  -F "archivo=@/ruta/a/tu/foto.jpg"
```

### Procesar imagen

```bash
curl -X POST http://localhost:8000/api/imagenes/UUID_DE_LA_FOTO/procesar/ \
  -H "Content-Type: application/json" \
  -d '{
    "token_publico": "TOKEN_PUBLICO"
  }'
```

### Generar figurita

```bash
curl -X POST http://localhost:8000/api/sesiones/TOKEN_PUBLICO/figuritas/generar/ \
  -H "Content-Type: application/json" \
  -d '{
    "resultado_recorte_id": "UUID_DEL_RECORTE"
  }'
```

## Integracion con Gemini

- Toda la integracion vive en `imagenes/services/servicio_gemini.py`.
- Se usa el SDK oficial `google-genai`.
- Gemini devuelve segmentos de persona con `box_2d` y `mask`.
- El backend selecciona el mejor segmento de persona, reconstruye la mascara al tamano real, refina bordes con OpenCV y exporta un PNG transparente.
- Si `GEMINI_MODO_SIMULADO=True` y no hay clave valida, el backend usa una simulacion local para desarrollo.
- Publicamente el motor de IA sigue siendo Gemini; el refinado local es posprocesado tecnico.

## Admin

El admin permite gestionar:

- flujos de trivia activos
- preguntas, orden y validaciones
- catalogo de equipos
- sesiones anonimas
- respuestas guardadas
- datos normalizados del sticker
- fotos y estados de procesamiento
- plantillas de figurita
- figuritas generadas

## Pruebas

La suite cubre:

- creacion de sesion anonima
- obtencion de preguntas activas
- validacion de altura y fecha
- desbloqueo de carga de foto
- subida y procesamiento de imagen
- generacion de figurita
- verificacion de `DatosSticker` en el render final

Ejecutar:

```bash
python manage.py test
```
