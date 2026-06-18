#!/bin/sh
set -e

# Solo migrar y sembrar cuando el contenedor arranca como servidor web.
# Otros subcomandos (test, shell, check, etc.) se ejecutan directamente.
case "$*" in
  *runserver*)
    echo "[entrypoint] Aplicando migraciones..."
    python manage.py migrate --no-input

    echo "[entrypoint] Cargando datos de demo..."
    python manage.py seed_demo

    echo "[entrypoint] Iniciando servidor..."
    ;;
esac

exec "$@"
