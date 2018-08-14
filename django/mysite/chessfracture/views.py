from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect

from .models import Game
from .forms import FractureForm

from urllib.parse import urlparse

# Create your views here.


def index(request):
    form = FractureForm()

    ctx = {
        'latest_games': Game.objects.order_by('-lastmodified')[:5],
        'form': form,
    }
    return render(request, 'chessfracture/index.html', ctx)


def parse_pgn_url(url):
    url = urlparse(url)
    if url.scheme != 'https' or url.netloc != 'lichess.org':
        return HttpResponse('error')


def fracture(request):
    if request.method == 'POST':
        form = FractureForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            parse_pgn_url(url)

            return redirect('chessfracture:get', kwargs={'site': 'lichess', 'gameid': '1234'})
        else:
            # TODO
            pass
    else:
        # TODO
        pass


def get(request, site, gameid):
    out = Game.objects.filter(site=site, gameid=gameid)
    out = '<h1>get</h1>' + out
    return HttpResponse(out)
