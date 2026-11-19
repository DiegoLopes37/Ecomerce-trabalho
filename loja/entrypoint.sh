#!/bin/sh
set -e

echo "Aguardando o MySQL em ${DB_HOST}:${DB_PORT}..."
while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Cria o administrador inicial caso ainda não exista
python manage.py shell <<'EOF'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.environ.get("ADMIN_USER", "admin")
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u, os.environ.get("ADMIN_EMAIL", "admin@example.com"),
                                  os.environ.get("ADMIN_PASSWORD", "admin12345"))
    print("Administrador criado:", u)
EOF

exec "$@"
