from django.urls import path, re_path
from . import views
from . import api
app_name = 'app_controleur'
urlpatterns = [
    path('', views.controleur_form, name='controleur_form'),
    path('result/', views.controleur_result, name='controleur_result'),
    re_path(r'^API/occupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_siege, name='api_occupation_siege'),
    re_path(r'^message/occupationSiege/trainId=(?P<numero_train_commercial>[^&]+)&voiture=(?P<numero_voiture>[^&]+)&siege=(?P<numero_siege>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_siege, name='api_controleur_message'),

]