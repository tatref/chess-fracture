from django.shortcuts import render

from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from .models import Game

# Create your views here.


def index(request):
    ctx = {
        'latest_games': Game.objects.order_by('-lastmodified')[:5]
    }
    return render(request, 'chessfracture/index.html', ctx)
