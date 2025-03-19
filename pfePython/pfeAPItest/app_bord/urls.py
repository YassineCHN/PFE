from django.urls import path, re_path
from . import views
from . import api
app_name = 'app_bord'
urlpatterns = [
    path('', views.home, name='home'),  # Page d'accueil avec vignettes
    path('bord/', views.index, name='bord_index'),  # Formulaire BORD
    path('bord/result/', views.bord_result, name='bord_result'),  # Résultats BORD
    re_path(r'^API/occupationDesPlaces/(?P<numero_train_commercial>[^&]+)&(?P<station_id>[^&]+)&(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_des_places, name='api_occupation_des_places'),
    # Format message original (pour compatibilité)
    re_path(r'^message/reservations/trainId=(?P<numero_train_commercial>[^&]+)&stationId=(?P<station_id>[^&]+)&journeyDate=(?P<date_debut_mission>[^&]+)$',
        api.api_occupation_des_places, name='api_bord_message'),

#3
]