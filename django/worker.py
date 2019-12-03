#!/usr/bin/env python


TMPDIR = '/tmp/blender'


import sys, os
import subprocess
import zipfile
import io
import time
import signal
import resource
import chess.pgn

import django
from django.db import transaction
from django import db
from django.utils import timezone
import requests


sys.path.append('/home/{}/chessfracture/django/mysite'.format(os.environ['USER']))
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
django.setup()

from chessfracture.models import Game, Worker



worker = Worker()
worker.save()
print('Registred worker {}'.format(worker.id))
sys.stdout.flush()


class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
    
    def exit_gracefully(self, signum, frame):
        self.kill_now = True
        print('Received signal {}, will exit after simulation'.format(signum))
        sys.stdout.flush()

def set_child_limits():
    # 50M
    MEM_LIMIT = 300 * 1024 * 1024
    #resource.setrlimit(resource.RLIMIT_AS, (MEM_LIMIT, MEM_LIMIT))


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
    blender_exe = '/home/{}/blender-2.81-linux-glibc217-x86_64/blender'.format(os.environ['USER'])
    blend_template = '/home/{}/chessfracture/blender/chess_fracture_template_2.80.blend'.format(os.environ['USER'])
    blender_script = '/home/{}/chessfracture/blender/chess_fracture_2.80.py'.format(os.environ['USER'])
    timeout = 200

    env = {
            'DISPLAY': display,
            'MESA_GL_VERSION_OVERRIDE': '3.3',

            'CHESS_FRACTURE_OUT_BLEND': out_blend,
            'CHESS_FRACTURE_PGN_PATH': pgn_path,
            'CHESS_FRACTURE_FRAMES_PER_MOVE': '20',
            'CHESS_FRACTURE_FRAGMENTS': '5',
            }
    env.update(os.environ)

    if 'CHESS_FRACTURE_TEST' in os.environ:
        env['CHESS_FRACTURE_TEST'] = ''

    run_args = [
            blender_exe,
            blend_template,
            '-noaudio',
            '--addons',
            'object_fracture_cell',
            '--python',
            blender_script,
            ]

    popen = subprocess.Popen(
            run_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='/tmp',
            env=env,
            start_new_session=True,
            preexec_fn=set_child_limits,
            )
    try:
        stdout_data, stderr_data = popen.communicate(timeout=timeout)
        popen.stdout.close()
        popen.stderr.close()
    except Exception as e:
        raise Exception('Timeout ({}) exceeded for : {} - {}'.format(timeout, pgn_path, e))
    return popen, stdout_data, stderr_data


def run_simulations(games):
    for g in games:
        print('Running simulation for {}'.format(g))
        sys.stdout.flush()

        pgn_path = TMPDIR + os.sep + g.site + '_' + g.gameid + '.pgn'
        out_blend = TMPDIR + os.sep + g.site + '_' + g.gameid + '.blend'

        with open(pgn_path, 'w') as f:
            f.write(g.pgn)

        try:
            g.status = 3
            g.save()

            sim_start = timezone.now()
            blender_popen, stdout, stderr = run_simulation(pgn_path, out_blend)
            sim_duration = timezone.now() - sim_start
            g.simulation_duration = sim_duration
            g.save()

            if blender_popen.returncode != 0:
                print('Simulation failed: retcode={}, out={}, err={}'.format(blender_popen.returncode, stdout, stderr))
                sys.stdout.flush()
                g.status = -1
                db_error_message = "{}\nstdout:\n{}\nstderr:\{}".format(blender_popen, stdout, stderr)
                g.errormessage = db_error_message
                g.save()
                continue
            os.remove(pgn_path)

        except Exception as e:
            # unreachable if blender_popen was launched?
            print('Simulation failed: ' + str(e))
            sys.stdout.flush()
            g.status = -1
            g.errormessage = str(e)
            g.save()
            try:
                os.remove(pgn_path)
            except:
                pass
            try:
                os.remove(out_blend)
            except:
                pass
            continue

        try:
            compressed_blend = compress_file(out_blend)
            g.blend = compressed_blend.read()
            compressed_blend.close()
            g.status = 0
            g.save()
            os.remove(out_blend)
        except Exception as e:
            print('Saving compressed blend failed: ' + str(e))
            sys.stdout.flush()
            g.status = -1
            g.errormessage = str(e)
            g.save()
            try:
                os.remove(out_blend)
            except:
                pass
            continue
        print('Simulation done: {}'.format(g))
        sys.stdout.flush()


def download_lichess_pgn(gameid):
    base_url = 'https://lichess.org/game/export/'
    url = base_url  + gameid
    r = requests.get(url)
    if not r.ok:
        raise Exception('PGN download failed, status_code={}'.format(r.status_code))
    pgn = r.text

    return pgn


def save_pgn(game):
    if game.site == 'lichess.org':
        try:
            pgn_data = download_lichess_pgn(game.gameid)
        except Exception as e:
            game.status = -1
            game.errormessage = str(e)
            game.save()
            print('Download failed for {}: {}'.format(game, e))
            sys.stdout.flush()
            return
    else:
        game.status = -1
        game.errormessage = 'Unknown site {}'.format(game.site)
        game.save()
        print('Download failed for {}: unknown site: {}'.format(game, game.site))
        sys.stdout.flush()
        return

    chess_game = chess.pgn.read_game(io.StringIO(pgn_data))
    game.white = chess_game.headers['White']
    game.black = chess_game.headers['Black']
    game.utcdate = chess_game.headers['UTCDate'].replace('.', '-') + ' ' + chess_game.headers['UTCTime'] + '+00:00'

    game.pgn = pgn_data
    game.status = 2
    game.save()


def save_pgns(games):
    for g in games:
        save_pgn(g)


def assign_woker():
    with transaction.atomic():
        game = Game.objects.filter(status=1, worker=None) \
            .order_by('submitdate') \
            .select_for_update() \
            .first()
        if game:
            game.worker = worker
            game.save()
            print('{} assigned to worker {}#'.format(game, worker.id))
            sys.stdout.flush()


def new_games_loop():
    # download PGN: 1 -> 2
    new_games = Game.objects.filter(status=1, worker=worker) \
        .order_by('submitdate')

    save_pgns(new_games)


def simulations_loop():
    # run simulation: 2 -> 3 -> 0
    need_simulation = Game.objects.filter(status=2, worker=worker) \
        .order_by('submitdate')
    run_simulations(need_simulation)


if __name__ == '__main__':
    killer = GracefulKiller()

    while not killer.kill_now:
        assign_woker()
        new_games_loop()
        simulations_loop()

        time.sleep(1)
        worker.save()
        db.reset_queries()
    print('Exiting')
    sys.stdout.flush()

