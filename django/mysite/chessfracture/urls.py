from django.urls import path

from . import views

app_name = 'chessfracture'
urlpatterns = [
    path('', views.index, name='index'),
]
