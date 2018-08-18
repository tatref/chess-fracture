#!/usr/bin/env python


import sys, os
import django

sys.path.append('/home/ansible/chess-fracture/django/mysite')
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()


from chessfracture.models import Game


games = Game.objects.all()

for g in games:
    print(g)
