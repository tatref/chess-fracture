import re
from urllib.parse import urlparse
import datetime

from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from .models import Game, Worker
from .forms import FractureForm

# Create your views here.


def index(request):
    form = FractureForm()

    ctx = {
        'latest_games': Game.objects.filter(status=0).order_by('-submitdate')[:10],
        'form': form,
    }
    return render(request, 'chessfracture/index.html', ctx)


'''
    1) validate URL
    2) return site, gameid
'''
def parse_pgn_url(url):
    url = urlparse(url)
    if url.netloc != 'lichess.org':
        raise Exception('Invalid site')
    path = url.path
    # https://lichess.org/xxxxx/white#2
    r = re.compile(r'^/(?P<gameid>\w+)(?:/(white|black)?)?')
    m = r.match(path)
    if m:
        gameid, color = m.groups()
    else:
        raise Exception('Wrong URL must be "https://lichess.org/xxxxx/white#2"')

    return 'lichess.org', gameid


def fracture(request):
    if request.method != 'POST':
        context = { 'error_message': 'Must be POST, not GET' }
        return render(request, 'chessfracture/error.html', context)

    form = FractureForm(request.POST)
    if not form.is_valid():
        #TODO: log
        context = { 'error_message': 'Invalid request: form is not valid ' + str(request.POST) }
        return render(request, 'chessfracture/error.html', context)

    url = form.cleaned_data['url']
    try:
        site, gameid = parse_pgn_url(url)
    except Exception as e:
        context = { 'error_message': str(e) }
        return render(request, 'chessfracture/error.html', context)

    game = Game.objects.filter(site=site, gameid=gameid)
    if game.exists():
        pass
    else:
        game = Game(site=site, gameid=gameid, status=1)
        game.save()

    return redirect('get/{}/{}'.format(site, gameid))
    #return redirect('chessfracture:get', kwargs={'site': site, 'gameid': gameid})


def get(request, site, gameid):
    data = Game.objects.filter(site=site, gameid=gameid)
    if not data:
        context = { 'error_message': 'Game not found' }
        return render(request, 'chessfracture/error.html', context)

    game = data[0]

    if game.status == 0:
        # done
        game.lastdl = timezone.now()
        game.save()

        response = HttpResponse(content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename={}_{}.blend.zip'.format(site, gameid)
        response.write(game.blend.tobytes())
        return response
    elif game.status == 1:
        # new
        context = { 'status': game.status}
        return render(request, 'chessfracture/refresh.html', context)
    elif game.status == 2:
        # pgn_downloaded
        context = { 'status': game.status}
        return render(request, 'chessfracture/refresh.html', context)
    elif game.status == 3:
        # simulating
        context = { 'status': game.status}
        return render(request, 'chessfracture/refresh.html', context)
    elif game.status == -1:
        # failed
        error_message = game.errormessage
        context = { 'error_message': 'Simulation failed (unsupported PGN?): {}'.format(error_message) }
        return render(request, 'chessfracture/error.html', context)
    else:
        # unknown status???
        context = { 'error_message': 'Unknown game state: {}'.format(game.status) }
        return render(request, 'chessfracture/error.html', context)
    # unreachable


def monitoring(request):
    total_games = Game.objects.all().count()
    failed_games = Game.objects.filter(status=-1).count()
    queued_games = Game.objects.filter(status=1).count()
    simulation_finished_games = Game.objects.filter(status=0).count()

    data = {}
    data['games'] = {
        'total': total_games,
        'failed': failed_games,
        'queued': queued_games,
        'finished': simulation_finished_games,
    }

    threshold = 5 * 60
    active_threshold = timezone.now() - datetime.timedelta(seconds=threshold)
    active_workers = Worker.objects.filter(heartbeat__gt=active_threshold).count()

    data['workers'] = {
        'active': active_workers,
    }

    response = JsonResponse(data)
    return response
