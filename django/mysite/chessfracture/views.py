from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect

from .models import Game
from .forms import FractureForm

import re
from urllib.parse import urlparse

# Create your views here.


def index(request):
    form = FractureForm()

    ctx = {
        'latest_games': Game.objects.order_by('-submitdate')[:5],
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
    r = re.compile(r'^/(?P<gameid>\w+)(?:/(white|black)?)')
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
        game = Game(site=site, gameid=gameid, status=0)
        game.save()

    return redirect('get/{}/{}'.format(site, gameid))
    #return redirect('chessfracture:get', kwargs={'site': site, 'gameid': gameid})


def get(request, site, gameid):
    out = '<h1>get</h1>'

    data = Game.objects.filter(site=site, gameid=gameid)
    if not data:
        context = { 'error_message': 'Game not found (submit first?)' }
        return render(request, 'chessfracture/error.html', context)

    game = data[0]

    if game.status == 0:
        # new
        pass
    elif game.status == 1:
        # simulating
        pass
    elif game.status == 2:
        # done
        response = HttpResponse(content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename={}_{}.blend'.format(site, gameid)
        response.write(game.blend.tobytes())
        return response
    elif game.status == -1:
        # failed
        print(game.errormessage)
        pass

    return HttpResponse('hello')
