"""
URL configuration for pfeAPItest project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include,re_path
from django.views.generic import RedirectView 
from app_gestionnaire import api as gestionnaire_api
from app_controleur import api as controleur_api
from app_bord import api as bord_api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("bord/", include("app_bord.urls")),
    path("controleur/", include("app_controleur.urls")),
    path("gestionnaire/", include("app_gestionnaire.urls")),
    
    # Ajoutez l'une des options suivantes pour gérer l'URL racine :
    
    # Option 1: Rediriger vers l'application bord
    #path("", RedirectView.as_view(url="/bord/", permanent=False)),
    path("", include("common_utils.urls")),  
    # Ou Option 2: Rediriger vers l'application gestionnaire
    
    # path("", RedirectView.as_view(url="/gestionnaire/", permanent=False)),
    
    # Ou Option 3: Inclure directement les URLs d'une application
    # path("", include("app_bord.urls")),
    # Maintenir les anciennes URL d'API à la racine pour la rétrocompatibilité
    #re_path(r'^API/tauxOccupation/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
     #   gestionnaire_api.api_taux_occupation_global, name='root_api_taux_occupation_global'),
    
    #re_path(r'^API/occupationDesPlaces/(?P<numero_train_commercial>[^&]+)&(?P<station_id>[^&]+)&(?P<date_debut_mission>[^&]+)$',
     #   bord_api.api_occupation_des_places, name='root_api_occupation_des_places'),
    
   # re_path(r'^API/occupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
    #    controleur_api.api_occupation_siege, name='root_api_occupation_siege'),
    
    # Ajouter ici les autres routes d'API qui doivent être accessibles à la racine
    re_path(r'^API/tauxOccupationDesserte/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_desserte, name='root_api_taux_occupation_desserte'),
    
    re_path(r'^API/tauxOccupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_siege, name='root_api_taux_occupation_siege'),
    
    re_path(r'^API/tauxOccupationVoiture/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_voiture, name='root_api_taux_occupation_voiture'),
    
    re_path(r'^API/tauxOccupationDesserteSpecifique/(?P<numero_train_commercial>[^&]+)&(?P<code_uic_desserte>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_desserte_specifique, name='root_api_taux_occupation_desserte_specifique'),
    
    re_path(r'^API/exportCSV/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_export_csv, name='root_api_export_csv'),
    
    re_path(r'^API/fluxPassagers/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_passager_flow, name='root_api_passager_flow'),
    
    # Même chose pour les routes message
    re_path(r'^message/reservations/trainId=(?P<numero_train_commercial>[^&]+)&stationId=(?P<station_id>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$',
        bord_api.api_occupation_des_places, name='root_api_bord_message'),
    
    re_path(r'^message/occupationSiege/trainId=(?P<numero_train_commercial>[^&]+)&voiture=(?P<numero_voiture>[^&]+)&siege=(?P<numero_siege>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$',
        controleur_api.api_occupation_siege, name='root_api_controleur_message'),

    
]