#!/usr/bin/env bash

echo "Aplicando migraciones..."
python manage.py migrate --noinput

echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Iniciando servidor..."
gunicorn statsprime.wsgi:application --bind 0.0.0.0:$PORT
