from django.urls import path, re_path

from . import views

app_name = 'chessfracture'
urlpatterns = [
    path('', views.index, name='index'),
    path('fracture', views.fracture, name='fracture'),
    path('monitoring', views.monitoring, name='monitoring'),
    re_path(r'^get/(?P<site>[\w.]+)/(?P<gameid>\w+)/', views.get, name='get'),
    #path('get/<slug:site>/<slug:gameid>', views.get, name='get'),
]
