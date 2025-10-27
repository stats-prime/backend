#!/usr/bin/env bash
echo "🧹 Limpiando base de datos..."
python manage.py flush --noinput || echo "⚠️ No se pudo limpiar la base"

echo "🧱 Creando migraciones..."
python manage.py makemigrations --noinput || echo "⚠️ Error al crear migraciones"

echo "🗂 Aplicando migraciones..."
python manage.py migrate --noinput

echo "📦 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "📥 Cargando fixtures..."
python manage.py loaddata farm/fixtures/farm_games.json || echo "⚠️ No se pudo cargar farm_games.json"
python manage.py loaddata farm/fixtures/farm_sources_genshin.json || echo "⚠️ No se pudo cargar farm_sources_genshin.json"
python manage.py loaddata farm/fixtures/farm_rewards_genshin.json || echo "⚠️ No se pudo cargar farm_rewards_genshin.json"

echo "🚀 Iniciando servidor..."
gunicorn statsprime.wsgi:application --bind 0.0.0.0:$PORT
