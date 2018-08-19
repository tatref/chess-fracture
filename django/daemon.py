#!/usr/bin/env python


import sys, os
import django

sys.path.append('/home/ansible/chess-fracture/django/mysite')
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()


from chessfracture.models import Game


games = Game.objects.all()

def purge_old_games(delay):
    for old_game in Game.objects.filter(lastdl__le=(timezone.now() - timezone.timedelta(seconds=delay))):
        old_game.delete()
