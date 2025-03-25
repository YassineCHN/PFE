from django.urls import path, re_path
from . import views

from app_gestionnaire import api as gestionnaire_api

app_name = 'app_gestionnaire'
urlpatterns = [
    path('', views.gestionnaire_form, name='gestionnaire_form'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('normalize/', views.normalize_json_page, name='normalize_json_page'),
    path('find-station/<str:uic_code>/', views.find_station, name='find_station'),
    # Ajoutez toutes les URLs du gestionnaire ici
    re_path(r'^API/tauxOccupation/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_global, name='api_taux_occupation_global'),
    re_path(r'^API/tauxOccupationDesserteSpecifique/(?P<numero_train_commercial>[^&]+)&(?P<code_uic_desserte>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_desserte_specifique, name='api_taux_occupation_desserte_specifique'),
    re_path(r'^API/exportCSV/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_export_csv, name='api_export_csv'),
    re_path(r'^API/tauxOccupationDesserte/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_desserte, name='api_taux_occupation_desserte'),
    re_path(r'^API/tauxOccupationVoiture/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_voiture, name='api_taux_occupation_voiture'),
    re_path(r'^API/tauxOccupationSiege/(?P<numero_train_commercial>[^&]+)&(?P<numero_voiture>[^&]+)&(?P<numero_siege>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_siege, name='api_taux_occupation_siege'),
    re_path(r'^API/fluxPassagers/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_passager_flow, name='api_passager_flow'),
    re_path(r'^API/tauxOccupationVoitureGlobal/(?P<numero_train_commercial>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        gestionnaire_api.api_taux_occupation_voiture_global, name='api_taux_occupation_voiture_global'),
  
    
]