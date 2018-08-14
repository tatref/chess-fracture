from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from .models import Question


def index(request):
    ctx = {
        'latest_question_list': Question.objects.order_by('-pub_date')[:5]
    }
    return render(request, 'polls/index.html', ctx)

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'polls/detail.html', {'question': question})

def results(request, question_id):
    return HttpResponse('results for question {}'.format(question_id))

def vote(request, question_id):
    return HttpResponse('voting for question {}'.format(question_id))
