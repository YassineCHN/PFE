

import json
import os
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .views import load_json_file, get_station_name, get_seat_occupation

def api_occupation_des_places(request, numero_train_commercial, date_debut_mission):
    """
    API pour récupérer les données d'occupation des places d'un train
    
    URL: /API/occupationDesPlaces/<numero_train_commercial>&<date_debut_mission>
    
    Returns:
        JsonResponse: Les données d'occupation des places au format JSON
    """
    # Chemin du fichier JSON
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    file_path = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    
    # Chargement des données
    train_data = load_json_file(file_path)
    
    if not train_data:
        return JsonResponse({"error": "Aucune donnée d'occupation des places disponible"}, status=404)
    
    # Retourne les données brutes au format JSON
    return JsonResponse(train_data)

def api_occupation_siege(request, numero_train_commercial, numero_voiture, numero_siege, date_debut_mission):
    """
    API pour récupérer l'occupation d'un siège sur l'ensemble du trajet
    
    URL: /API/occupationSiege/<numero_train_commercial>&<numero_voiture>&<numero_siege>&<date_debut_mission>
    
    Returns:
        HttpResponse: Les données d'occupation du siège au format texte
    """
    result = get_seat_occupation(numero_siege, numero_voiture, numero_train_commercial, date_debut_mission)
    return HttpResponse(result, content_type='text/plain; charset=utf-8')

def api_occupation_gare(request, numero_train_commercial, code_uic_gare, date_debut_mission):
    """
    API pour récupérer l'occupation des places pour une gare donnée
    
    URL: /API/occupationGare/<numero_train_commercial>&<code_uic_gare>&<date_debut_mission>
    
    Returns:
        HttpResponse: Les données d'occupation des places pour la gare au format texte
    """
    # Récupérer les données du train
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    stations_file = f"{data_folder}Référentiel_stations.json"
    
    train_data = load_json_file(train_file)
    stations_data = load_json_file(stations_file)
    
    if not train_data or not stations_data:
        return HttpResponse("Aucune donnée d'occupation des places disponible", content_type='text/plain; charset=utf-8')
    
    # Trouver la desserte correspondant à la gare demandée
    target_desserte = None
    for desserte in train_data.get("dessertes", []):
        if desserte.get("codeUIC") == code_uic_gare:
            target_desserte = desserte
            break
    
    if not target_desserte:
        return HttpResponse(f"Aucune desserte trouvée pour la gare {code_uic_gare}", content_type='text/plain; charset=utf-8')
    
    # Placeholder - La logique complète de la fonctionnalité 1 devrait être implémentée ici
    # Ceci est une implémentation simplifiée pour démontrer l'API
    
    response_text = "Occupation des places pour la gare:\n"
    
    for rame in target_desserte.get("rames", []):
        for voiture in rame.get("voitures", []):
            voiture_num = voiture.get("numero")
            for place in voiture.get("places", []):
                place_num = place.get("numero")
                occupation = place.get("occupation", {})
                statut = occupation.get("statut", "INCONNU")
                
                response_text += f"seat.coach = {voiture_num}\n"
                response_text += f"seat.idSeat = {place_num}\n"
                response_text += f"seat.status = {statut}\n\n"
    
    return HttpResponse(response_text, content_type='text/plain; charset=utf-8')

def api_taux_occupation(request, numero_train_commercial, date_debut_mission):
    """
    API pour récupérer le taux d'occupation d'un train
    
    URL: /API/tauxOccupation/<numero_train_commercial>&<date_debut_mission>
    
    Returns:
        JsonResponse: Le taux d'occupation du train au format JSON
    """
    # Récupérer les données du train
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    
    train_data = load_json_file(train_file)
    
    if not train_data:
        return JsonResponse({"error": "Aucune donnée d'occupation des places disponible"}, status=404)
    
    # Placeholder - La logique complète de la fonctionnalité 3 devrait être implémentée ici
    # Ceci est une implémentation simplifiée pour démontrer l'API
    
    # Calcul simplifié du taux d'occupation
    total_seats = 0
    occupied_seats = 0
    
    # Comptabiliser les sièges occupés sur l'ensemble du trajet
    all_seats = {}  # Dictionnaire pour suivre les sièges {voiture_place: occupation}
    
    for desserte in train_data.get("dessertes", []):
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                for place in voiture.get("places", []):
                    seat_id = f"{voiture.get('numero')}_{place.get('numero')}"
                    occupation = place.get("occupation", {})
                    statut = occupation.get("statut")
                    
                    if seat_id not in all_seats:
                        all_seats[seat_id] = False
                    
                    if statut == "OCCUPE":
                        all_seats[seat_id] = True
    
    # Calculer le taux d'occupation
    total_seats = len(all_seats)
    occupied_seats = sum(1 for occupied in all_seats.values() if occupied)
    
    occupation_rate = 0
    if total_seats > 0:
        occupation_rate = (occupied_seats / total_seats) * 100
    
    result = {
        "train_number": numero_train_commercial,
        "journey_date": date_debut_mission,
        "total_seats": total_seats,
        "occupied_seats": occupied_seats,
        "occupation_rate": round(occupation_rate, 2)
    }
    
    return JsonResponse(result)