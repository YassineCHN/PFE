# -*- coding: utf-8 -*-


from django.contrib import admin
from django.urls import path, re_path
from testAAAversion1 import views
from testAAAversion1 import api


urlpatterns = [
    path("admin/", admin.site.urls),
    # URLs pour l'interface web
    path('', views.index, name='index'),
    path('controleur/', views.controleur_form, name='controleur_form'),
    path('controleur/result/', views.controleur_result, name='controleur_result'),
    path('bord/', views.bord_form, name='bord_form'),
    path('gestionnaire/', views.gestionnaire_form, name='gestionnaire_form'),
    
    # URLs du format demandé dans le cahier des charges original (message/*)
    re_path(r'^message/occupationSiege/trainId=(?P<numero_train_commercial>[^&]+)&voiture=(?P<numero_voiture>[^&]+)&siege=(?P<numero_siege>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$', 
        views.occupation_siege, name='occupation_siege'),
    
    # Nouvelles routes API avec le format demandé
    re_path(r'^API/occupationDesPlaces/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_des_places, name='api_occupation_des_places'),
    
    re_path(r'^API/occupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_siege, name='api_occupation_siege'),
    
    re_path(r'^API/occupationGare/(?P<numero_train_commercial>[^&]+)&(?P<code_uic_gare>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_gare, name='api_occupation_gare'),
    
    re_path(r'^API/tauxOccupation/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_taux_occupation, name='api_taux_occupation'),
    
   ##re_path(r'^message/occupationSiege/trainId=(?P<numero_train_commercial>[^&]+)&voiture=(?P<numero_voiture>[^&]+)&siege=(?P<numero_siege>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$', 
     ##  views.occupation_siege, name='occupation_siege'),
]