#!/usr/bin/env bash


. ~/django_venv/bin/activate


set -eu


#yes yes | ./manage.py  flush


./manage.py makemigrations
./manage.py migrate

echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@myproject.com', 'admin')" | python manage.py shell

