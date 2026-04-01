#!/bin/sh
set -e

echo "Esperando la base de datos..."
python - <<'PY'
import os
import time
import psycopg

host = os.environ["POSTGRES_HOST"]
port = os.environ["POSTGRES_PORT"]
dbname = os.environ["POSTGRES_DB"]
user = os.environ["POSTGRES_USER"]
password = os.environ["POSTGRES_PASSWORD"]

for intento in range(30):
    try:
        with psycopg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=3,
        ):
            print("Base de datos lista")
            break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("No fue posible conectar con PostgreSQL.")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
