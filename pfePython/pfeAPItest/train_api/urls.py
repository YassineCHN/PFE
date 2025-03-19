from django.urls import path, re_path
from . import views
from . import api

urlpatterns = [
    # URLs pour l'interface web
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('controleur/', views.controleur_form, name='controleur_form'),
    path('controleur/result/', views.controleur_result, name='controleur_result'),
    path('gestionnaire/', views.gestionnaire_form, name='gestionnaire_form'),
    # Nouvelle URL pour la page de normalisation JSON (simplifiée)
    path('normalize/', views.normalize_json_page, name='normalize_json_page'),
    # URL pour la recherche de gare par code UIC
    path('find-station/<str:uic_code>/', views.find_station, name='find_station'),
    # URLs API
    re_path(r'^API/occupationDesPlaces/(?P<numero_train_commercial>[^&]+)&(?P<station_id>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_des_places, name='api_occupation_des_places'),
    # URLs API pour la fonctionnalité 2: Contrôleur - Occupation d'un siège sur l'ensemble du trajet
    re_path(r'^API/occupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_siege, name='api_occupation_siege'),
    re_path(r'^API/fluxPassagers/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
    api.api_passager_flow, name='api_passager_flow'),
    # URLs API pour la fonctionnalité 3: Gestionnaire - Taux d'occupation
    # Taux d'occupation global
    re_path(r'^API/tauxOccupation/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_taux_occupation_global, name='api_taux_occupation_global'),
    
    # Taux d'occupation d'un siège
    re_path(r'^API/tauxOccupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_taux_occupation_siege, name='api_taux_occupation_siege'),
    
    # Taux d'occupation d'une voiture
    re_path(r'^API/tauxOccupationVoiture/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_taux_occupation_voiture, name='api_taux_occupation_voiture'),
    
    # Taux d'occupation par desserte
    re_path(r'^API/tauxOccupationDesserte/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_taux_occupation_desserte, name='api_taux_occupation_desserte'),
    
    # Export CSV
    re_path(r'^API/exportCSV/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_export_csv, name='api_export_csv'),
    
    # Format message original (pour compatibilité)
    re_path(r'^message/reservations/trainId=(?P<numero_train_commercial>[^&]+)&stationId=(?P<station_id>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_des_places, name='api_bord_message'),
        
    re_path(r'^message/occupationSiege/trainId=(?P<numero_train_commercial>[^&]+)&voiture=(?P<numero_voiture>[^&]+)&siege=(?P<numero_siege>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_siege, name='api_controleur_message'),
    re_path(r'^API/tauxOccupationDesserteSpecifique/(?P<numero_train_commercial>[^&]+)&(?P<code_uic_desserte>[^&]+)&(?P<date_debut_mission>[^&]+)$',
    api.api_taux_occupation_desserte_specifique, name='api_taux_occupation_desserte_specifique'),
   # re_path(r'^API/occupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
    #    api.api_occupation_siege, name='api_occupation_siege'),
    # Format message original (pour compatibilité)
    #re_path(r'^message/reservations/trainId=(?P<numero_train_commercial>[^&]+)&stationId=(?P<station_id>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$',
     #   api.api_occupation_des_places, name='api_bord_message'),
        
   # re_path(r'^message/occupationSiege/trainId=(?P<numero_train_commercial>[^&]+)&voiture=(?P<numero_voiture>[^&]+)&siege=(?P<numero_siege>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$',
    #    api.api_occupation_siege, name='api_controleur_message'),
]