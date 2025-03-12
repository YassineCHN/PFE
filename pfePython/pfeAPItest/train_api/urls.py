from django.urls import path, re_path
from . import views
from . import api

urlpatterns = [
    # URLs pour l'interface web
    path('', views.index, name='index'),
    path('controleur/', views.controleur_form, name='controleur_form'),
    path('controleur/result/', views.controleur_result, name='controleur_result'),
    
    # URLs API
    re_path(r'^API/occupationDesPlaces/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_des_places, name='api_occupation_des_places'),
    
    re_path(r'^API/occupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_siege, name='api_occupation_siege'),
]