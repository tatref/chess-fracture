#!/usr/bin/env python


import sys, os
import django
import requests


sys.path.append('/home/ansible/chessfracture/django/mysite')
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()


from chessfracture.models import Game


games = Game.objects.all()

def purge_old_games(delay):
    for old_game in Game.objects.filter(lastdl__le=(timezone.now() - timezone.timedelta(seconds=delay))):
        old_game.delete()


def run_simulation(pgn_path, out_blend, display=':1'):
    blender_exe = '/home/{}/blender-2.79b-linux-glibc219-x86_64/blender'.format(os.environ['USER'])
    blend_template = '/home/{}/chessfracture/blender/chess_fracture_template.blend'.format(os.environ['USER'])
    blender_script = '/home/{}/chessfracture/blender/chess_fracture.py'.format(os.environ['USER'])
    timeout = 10

    env = {
        'CHESS_FRACTURE_OUT_BLEND': out_blend,
        'DISPLAY': display,
        'CHESS_FRACTURE_PGN_PATH': pgn_path,
        'CHESS_FRACTURE_TEST': '',
        'CHESS_FRACTURE_FRAMES_PER_MOVE': '20',
        'CHESS_FRACTURE_FRAGMENTS': '10',
            }

    run_args = [
            blender_exe,
            blend_template,
            '-noaudio',
            '--addons',
            'object_fracture_cell',
            '--python',
            blender_script,
            ]

    subprocess.run(
            run_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd='/tmp',
            env=env
            )

def run_simulations(games):
    for g in games:
        print('Running simulation for {}'.format(g))
        #run_simulation()


def download_lichess_pgn(gameid):
    base_url = 'https://lichess.org/game/export/'
    url = base_url  + gameid
    r = requests.get(url)
    pgn = r.content

    return pgn


def save_pgn(game):
    if game.site == 'lichess.org':
        pgn = download_lichess_pgn(game.gameid)
    else:
        print('unknown site')
        sys.exit(1)

    game.pgn = pgn
    game.save()


def save_pgns(games):
    for g in games:
        save_pgn(g)


def new_games_loop():
    new_games = Game.objects.filter(status=0).order_by('submitdate')

    save_pgns(new_games)

def simulations_loop():
    need_simulation = Game.objects.filter(status=1).order_by('submitdate')
    run_simulations(need_simulation)
