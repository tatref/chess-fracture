from django.urls import path

from . import views

app_name = 'chessfracture'
urlpatterns = [
    path('', views.index, name='index'),
    path('fracture', views.fracture, name='fracture'),
    path('get/<slug:site>/<slug:gameid>', views.get, name='get'),
]
