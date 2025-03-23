# app_bord/views.py
from django.shortcuts import render

import os
from django.conf import settings
from common_utils.utils.json_utils import load_json_file,get_station_name
from django.shortcuts import  redirect


def home(request):
    """
    Vue de la page d'accueil avec les vignettes de navigation
    """
    return render(request, 'app_bord/bord_index.html')

def bord_result(request):
    """
    Vue pour traiter le formulaire et afficher les résultats de l'occupation des places
    """
    if request.method == 'POST':
        train_number = request.POST.get('train_number')
        journey_date = request.POST.get('journey_date')
        station_id = request.POST.get('station_id')
        
        # Récupération des données d'occupation (simulée ici)
        data_folder = os.path.join(settings.BASE_DIR, 'data/')
        stations_file = f"{data_folder}Référentiel_stations.json"
        
        # Récupérer le nom de la gare si disponible
        stations_data = load_json_file(stations_file)
        station_name = get_station_name(station_id, stations_data) if stations_data else None
        
        # Appel à l'API d'occupation des places (version réelle)
        # si on voulait vraiment simuler l'appel à l'API, on pourrait le faire avec du javascript
        # a voir pour les besoins de la présentation
        from app_bord.api import api_occupation_des_places
        
        # Créer une requête factice pour l'API
        from django.http import HttpRequest
        api_request = HttpRequest()
        
        # Appeler l'API directement
        api_response = api_occupation_des_places(api_request, train_number, station_id, journey_date)
        
        # Récupérer le contenu textuel de la réponse HTTP
        occupation_data = api_response.content.decode('utf-8')
        
        context = {
            'train_number': train_number,
            'journey_date': journey_date,
            'station_id': station_id,
            'station_name': station_name,
            'occupation_data': occupation_data
        }
        
        return render(request, 'app_bord/bord_result.html', context)
    
    # Redirection vers le formulaire en cas d'accès direct à cette URL
    return redirect('app_bord:home')