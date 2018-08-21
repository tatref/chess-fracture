#!/usr/bin/env python


TMPDIR = '/tmp/blender'


import sys, os
import subprocess
import zipfile
import io

import django
import requests


sys.path.append('/home/{}/chessfracture/django/mysite'.format(os.environ['USER']))
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()


from chessfracture.models import Game


games = Game.objects.all()




def purge_old_games(delay):
    for old_game in Game.objects.filter(lastdl__le=(timezone.now() - timezone.timedelta(seconds=delay))):
        old_game.delete()


def compress_file(f_in):
    # in-memory
    mem = io.BytesIO()

    with zipfile.ZipFile(mem, mode='w', compression=zipfile.ZIP_LZMA) as zip:
        arcname = os.path.basename(f_in)
        zip.write(f_in, arcname=arcname)

    mem.seek(0)
    return mem

def run_simulation(pgn_path, out_blend, display=':1'):
    blender_exe = '/home/{}/blender-2.79b-linux-glibc219-x86_64/blender'.format(os.environ['USER'])
    blend_template = '/home/{}/chessfracture/blender/chess_fracture_template.blend'.format(os.environ['USER'])
    blender_script = '/home/{}/chessfracture/blender/chess_fracture.py'.format(os.environ['USER'])
    timeout = 100

    env = os.environ

    env.update(
        {
        'CHESS_FRACTURE_OUT_BLEND': out_blend,
        'DISPLAY': display,
        'CHESS_FRACTURE_PGN_PATH': pgn_path,
        'CHESS_FRACTURE_TEST': '',
        'CHESS_FRACTURE_FRAMES_PER_MOVE': '20',
        'CHESS_FRACTURE_FRAGMENTS': '10',
        }
    )

    run_args = [
            blender_exe,
            blend_template,
            '-noaudio',
            '--addons',
            'object_fracture_cell',
            '--python',
            blender_script,
            ]

    blender = subprocess.run(
            run_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd='/tmp',
            env=env
            )
    return blender

def run_simulations(games):
    for g in games:
        print('Running simulation for {}'.format(g))

        pgn_path = TMPDIR + os.sep + g.site + '_' + g.gameid + '.pgn'
        out_blend = TMPDIR + os.sep + g.site + '_' + g.gameid + '.blend'

        with open(pgn_path, 'w') as f:
            f.write(g.pgn)

        try:
            blender = run_simulation(pgn_path, out_blend)
            from pprint import pprint
            pprint(blender)
        except Exception as e:
            print('Simulation failed: ' + str(e))
            g.status = -1
            g.errormessage = str(e)
            g.save
            continue

        try:
            compressed_blend = compress_file(out_blend)
            g.blend = compressed_blend.read()
            g.status = 0
            g.save()
        except Exception as e:
            print('Saving compressed blend failed: ' + str(e))
            g.status = -1
            g.errormessage = str(e)
            g.save
            continue



def download_lichess_pgn(gameid):
    base_url = 'https://lichess.org/game/export/'
    url = base_url  + gameid
    r = requests.get(url)
    pgn = r.text

    return pgn


def save_pgn(game):
    if game.site == 'lichess.org':
        pgn = download_lichess_pgn(game.gameid)
    else:
        print('unknown site')
        sys.exit(1)

    game.pgn = pgn
    game.status = 2
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
