#!/usr/bin/env bash


yes yes | ./manage.py  flush

rm -f */migrations/0*.py

./manage.py makemigrations
./manage.py migrate

echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@myproject.com', 'admin')" | python manage.py shell

