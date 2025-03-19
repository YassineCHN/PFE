# app_bord/views.py
from django.shortcuts import render

import os, json
from django.conf import settings
from common_utils.utils.json_utils import load_json_file
from django.shortcuts import render, redirect
from django.http import HttpResponse

def index(request):
    """
    Page d'accueil pour le BORD
    """
    return render(request, 'app_bord/index.html')

def get_station_name(code_uic, stations_data):
    """
    Récupère le nom court de la gare à partir du code UIC
    """
    for station in stations_data:
        if station['codeUIC'] == code_uic:
            return station['shortLabel']
    return code_uic  # Retourne le code UIC si non trouvé

def home(request):
    """
    Vue de la page d'accueil avec les vignettes de navigation
    """
    return render(request, 'app_bord/bord_index.html')

def index(request):
    """
    Vue pour afficher le formulaire de consultation d'occupation des places par le BORD
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
        
        # Appel à l'API d'occupation des places (simulation simplifiée)
        # Normalement, vous appelleriez votre fonction api.api_occupation_des_places ici
        
        # Pour la démonstration, nous pouvons utiliser un texte de test
        occupation_data = """seat.coach = 1
        seat.idSeat = 2
        seat.beginStation = Paris Auster
        seat.endStation = Toulouse
        seat.coach = 1
        seat.idSeat = 4
        seat.beginStation = Limoges
        seat.endStation = Brive-la-G.
        seat.coach = 2
        seat.idSeat = 6
        seat.beginStation = Limoges
        seat.endStation = Montauban"""
        
        context = {
            'train_number': train_number,
            'journey_date': journey_date,
            'station_id': station_id,
            'station_name': station_name,
            'occupation_data': occupation_data
        }
        
        return render(request, 'app_bord/bord_result.html', context)
    
    # Redirection vers le formulaire en cas d'accès direct à cette URL
    return redirect('app_bord:bord_index')