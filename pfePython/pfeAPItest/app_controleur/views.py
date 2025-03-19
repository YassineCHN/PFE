
from django.shortcuts import render, redirect
from common_utils.utils.json_utils import load_json_file, get_station_name
from django.conf import settings
import os, json

def controleur_form(request):
    """
    Vue pour afficher le formulaire de recherche d'occupation de siège par le contrôleur
    """
    return render(request, 'app_controleur/controleur_form.html')
def get_seat_occupation(seat_number, coach_number, train_number, journey_date, data_folder=None):
    """
    Récupère les segments d'occupation d'un siège donné sur l'ensemble d'une course
    """
    if data_folder is None:
        data_folder = os.path.join(settings.BASE_DIR, 'data/')
    
    # Chargement des données
    train_file = f"{data_folder}{train_number}_{journey_date}.json"
    stations_file = f"{data_folder}Référentiel_stations.json"
    
    train_data = load_json_file(train_file)
    stations_data = load_json_file(stations_file)
    
    if not train_data or not stations_data:
        return "Aucune donnée d'occupation des places disponible"
    
    # Initialiser le tableau des segments d'occupation
    occupation_segments = []
    
    # Récupérer la liste des dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: x.get("rang"))
    
    # Variables pour suivre l'état d'occupation
    current_occupation = None
    is_occupied = False
    
    # Parcourir toutes les dessertes pour trouver le siège
    for desserte in dessertes:
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                if voiture.get("numero") == coach_number:
                    for place in voiture.get("places", []):
                        if place.get("numero") == seat_number:
                            occupation = place.get("occupation", {})
                            statut = occupation.get("statut")
                            flux_montant = occupation.get("fluxMontant", False)
                            flux_descendant = occupation.get("fluxDescendant", False)
                            
                            # Gérer le début d'une occupation
                            if flux_montant and not is_occupied:
                                current_occupation = {
                                    "begin_station_code": desserte.get("codeUIC"),
                                    "begin_station": get_station_name(desserte.get("codeUIC"), stations_data)
                                }
                                is_occupied = True
                            
                            # Gérer la fin d'une occupation
                            if flux_descendant and is_occupied:
                                current_occupation["end_station_code"] = desserte.get("codeUIC")
                                current_occupation["end_station"] = get_station_name(desserte.get("codeUIC"), stations_data)
                                occupation_segments.append(current_occupation)
                                is_occupied = False
                                current_occupation = None
                            
                            # Gérer le cas d'un changement de voyageur (descente et montée à la même desserte)
                            if flux_descendant and flux_montant:
                                # On termine l'occupation précédente si elle existe
                                if current_occupation and is_occupied:
                                    current_occupation["end_station_code"] = desserte.get("codeUIC")
                                    current_occupation["end_station"] = get_station_name(desserte.get("codeUIC"), stations_data)
                                    occupation_segments.append(current_occupation)
                                
                                # On commence une nouvelle occupation
                                current_occupation = {
                                    "begin_station_code": desserte.get("codeUIC"),
                                    "begin_station": get_station_name(desserte.get("codeUIC"), stations_data)
                                }
                                is_occupied = True
    
    # Gérer le cas où le trajet se termine avec une occupation en cours
    if is_occupied and current_occupation and dessertes:
        last_desserte = dessertes[-1]
        current_occupation["end_station_code"] = last_desserte.get("codeUIC")
        current_occupation["end_station"] = get_station_name(last_desserte.get("codeUIC"), stations_data)
        occupation_segments.append(current_occupation)
    
    # Formater la sortie selon le cahier des charges
    if not occupation_segments:
        return "Aucune occupation du siège détectée sur l'ensemble du trajet"
    
    # Construire la chaîne de réponse formatée
    formatted_output = ""
    formatted_output += f"seat.coach = {coach_number}\n"
    formatted_output += f"seat.idSeat = {seat_number}\n"
    
    for i, segment in enumerate(occupation_segments, 1):
        formatted_output += f"seat.numeroOccupation = {i}\n"
        formatted_output += f"seat.beginStation = {segment['begin_station']}\n"
        formatted_output += f"seat.endStation = {segment['end_station']}\n"
    
    return formatted_output

def controleur_result(request):
    """
    Vue pour traiter le formulaire et afficher les résultats de l'occupation d'un siège
    """
    if request.method == 'POST':
        train_number = request.POST.get('train_number')
        journey_date = request.POST.get('journey_date')
        coach_number = request.POST.get('coach_number')
        seat_number = request.POST.get('seat_number')
        
        # Appel à la fonction de traitement
        occupation_data = get_seat_occupation(seat_number, coach_number, train_number, journey_date)
        
        context = {
            'train_number': train_number,
            'journey_date': journey_date,
            'coach_number': coach_number,
            'seat_number': seat_number,
            'occupation_data': occupation_data
        }
        
        return render(request, 'app_controleur/controleur_result.html', context)
    
    # Redirection vers le formulaire en cas d'accès direct à cette URL
    return redirect('controleur_form')

    