# -*- coding: utf-8 -*-


import os
import csv

from io import StringIO
from django.http import HttpResponse, JsonResponse,FileResponse
from django.conf import settings
from train_api.utils.json_utils import load_json_file

def get_station_name(code_uic, stations_data):
    """
    Récupère le nom court de la gare à partir du code UIC
    """
    for station in stations_data:
        if station['codeUIC'] == code_uic:
            return station['shortLabel']
    return code_uic  # Retourne le code UIC si non trouvé

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

def api_occupation_des_places(request, numero_train_commercial, station_id, date_debut_mission):
    """
    API pour récupérer l'occupation des places pour une gare donnée (Fonctionnalité BORD)
    
    URL: /API/occupationDesPlaces/{numero_train_commercial}&{station_id}&{date_debut_mission}
    
    Returns:
        HttpResponse: Texte formaté avec l'occupation des places pour la gare demandée
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    stations_file = f"{data_folder}Référentiel_stations.json"
    
    train_data = load_json_file(train_file)
    stations_data = load_json_file(stations_file)
    
    if not train_data or not stations_data:
        return HttpResponse("Aucune donnée d'occupation des places disponible (le référentiel ou le jeu de données ne sont pas récupérables)", content_type='text/plain; charset=utf-8')
    
    # Récupérer toutes les dessertes triées par rang dans un tableau de json
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Trouver la desserte actuelle et son rang
    current_desserte = None
    current_rang = -1
    
    for desserte in dessertes:
        if desserte.get("codeUIC") == station_id:
            current_desserte = desserte
            current_rang = int(desserte.get("rang", 0))
            break
    
    if not current_desserte:
        return HttpResponse(f"Aucune desserte trouvée pour la gare {station_id}", content_type='text/plain; charset=utf-8')
    
    # Récupérer les dessertes futures (après la desserte actuelle)
    future_dessertes = [d for d in dessertes if int(d.get("rang", 0)) > current_rang]
    
    if not future_dessertes:
        return HttpResponse("Fin du trajet, aucune desserte future (à voir si on renvoit vide/rien)", content_type='text/plain; charset=utf-8')
    
    # Dictionnaire pour stocker les résultats
    seat_occupations = {}
    
    # On commence par traiter la desserte actuelle pour voir les places déjà occupées
    # et celles qui vont être occupées dans les dessertes futures
    
    # 1. Traiter la desserte actuelle pour connaître l'état initial des places
    current_seat_states = {}  # {coach_seat: is_occupied}
    
    for rame in current_desserte.get("rames", []):
        for voiture in rame.get("voitures", []):
            coach_number = voiture.get("numero")
            for place in voiture.get("places", []):
                seat_number = place.get("numero")
                seat_id = f"{coach_number}_{seat_number}"
                
                occupation = place.get("occupation", {})
                statut = occupation.get("statut", "LIBRE")
                
                current_seat_states[seat_id] = statut == "OCCUPE"
    
    # 2. Parcourir les dessertes futures pour trouver les prochaines occupations
    for desserte in future_dessertes:
        desserte_code_uic = desserte.get("codeUIC")
        
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                coach_number = voiture.get("numero")
                for place in voiture.get("places", []):
                    seat_number = place.get("numero")
                    seat_id = f"{coach_number}_{seat_number}"
                    
                    occupation = place.get("occupation", {})
                    statut = occupation.get("statut")
                    flux_montant = occupation.get("fluxMontant", False)
                    flux_descendant = occupation.get("fluxDescendant", False)
                    
                    # Cas 1: Siège actuellement LIBRE, et il y a un flux montant
                    if seat_id not in current_seat_states or not current_seat_states[seat_id]:
                        if flux_montant:
                            # Chercher où ce voyageur descendra
                            descend_station = None
                            descend_station_code = None
                            
                            # Chercher la fin de cette occupation
                            for future_desserte in [d for d in future_dessertes if int(d.get("rang", 0)) >= int(desserte.get("rang", 0))]:
                                for future_rame in future_desserte.get("rames", []):
                                    for future_voiture in future_rame.get("voitures", []):
                                        if future_voiture.get("numero") == coach_number:
                                            for future_place in future_voiture.get("places", []):
                                                if future_place.get("numero") == seat_number:
                                                    future_occupation = future_place.get("occupation", {})
                                                    future_flux_descendant = future_occupation.get("fluxDescendant", False)
                                                    
                                                    if future_flux_descendant:
                                                        descend_station_code = future_desserte.get("codeUIC")
                                                        descend_station = get_station_name(descend_station_code, stations_data)
                                                        break
                                            
                            # Si on a trouvé où le voyageur descend
                            if descend_station:
                                # Créer une entrée pour cette occupation
                                begin_station = get_station_name(desserte_code_uic, stations_data)
                                if seat_id not in seat_occupations:
                                    seat_occupations[seat_id] = {
                                        "coach": coach_number,
                                        "seat": seat_number,
                                        "begin_station": begin_station,
                                        "end_station": descend_station
                                    }
                            
                            # Mettre à jour l'état du siège
                            current_seat_states[seat_id] = True
                    
                    # Cas 2: Siège actuellement OCCUPE, et il y a un flux descendant
                    elif current_seat_states.get(seat_id, False):
                        if flux_descendant:
                            # Le siège devient libre
                            current_seat_states[seat_id] = False
                    
                    # Cas 3: Changement de voyageur (descente et montée à la même desserte)
                    if flux_descendant and flux_montant:
                        # On marque la descente du voyageur précédent
                        current_seat_states[seat_id] = False
                        
                        # Et on cherche où descendra le nouveau voyageur
                        descend_station = None
                        descend_station_code = None
                        
                        # Chercher la fin de cette nouvelle occupation
                        for future_desserte in [d for d in future_dessertes if int(d.get("rang", 0)) >= int(desserte.get("rang", 0))]:
                            for future_rame in future_desserte.get("rames", []):
                                for future_voiture in future_rame.get("voitures", []):
                                    if future_voiture.get("numero") == coach_number:
                                        for future_place in future_voiture.get("places", []):
                                            if future_place.get("numero") == seat_number:
                                                future_occupation = future_place.get("occupation", {})
                                                future_flux_descendant = future_occupation.get("fluxDescendant", False)
                                                
                                                if future_flux_descendant and future_desserte.get("codeUIC") != desserte_code_uic:
                                                    descend_station_code = future_desserte.get("codeUIC")
                                                    descend_station = get_station_name(descend_station_code, stations_data)
                                                    break
                        
                        # Si on a trouvé où le voyageur descend
                        if descend_station:
                            # Créer une entrée pour cette occupation
                            begin_station = get_station_name(desserte_code_uic, stations_data)
                            if seat_id not in seat_occupations:
                                seat_occupations[seat_id] = {
                                    "coach": coach_number,
                                    "seat": seat_number,
                                    "begin_station": begin_station,
                                    "end_station": descend_station
                                }
                        
                        # Mettre à jour l'état du siège
                        current_seat_states[seat_id] = True
    
    # Formater la réponse selon le cahier des charges
    response_text = ""
    
    for seat_id, occupation in seat_occupations.items():
        coach = occupation["coach"]
        seat = occupation["seat"]
        begin_station = occupation["begin_station"]
        end_station = occupation["end_station"]
        
        response_text += f"seat.coach = {coach}\n"
        response_text += f"seat.idSeat = {seat}\n"
        response_text += f"seat.beginStation = {begin_station}\n"
        response_text += f"seat.endStation = {end_station}\n"
    
    if not response_text:
        response_text = "Aucune occupation future des places disponible pour cette gare (à voir si on renvoie vide/rien)"
    
    return HttpResponse(response_text, content_type='text/plain; charset=utf-8')

def api_occupation_siege(request, numero_train_commercial, numero_voiture, numero_siege, date_debut_mission):
    """
    API pour récupérer l'occupation d'un siège sur l'ensemble du trajet
    """
    result = get_seat_occupation(numero_siege, numero_voiture, numero_train_commercial, date_debut_mission)
    return HttpResponse(result, content_type='text/plain; charset=utf-8')

def api_taux_occupation_global(request, numero_train_commercial, date_debut_mission):
    """
    API pour récupérer le taux d'occupation global d'un train
    
    URL: /API/tauxOccupation/<numero_train_commercial>&<date_debut_mission>
    
    Returns:
        JsonResponse: Taux d'occupation global du train
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    
    train_data = load_json_file(train_file)
    
    if not train_data:
        return JsonResponse({"error": "Aucune donnée d'occupation des places disponible"}, status=404)
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Dictionnaire pour suivre l'occupation de chaque siège sur tout le trajet
    all_seats = {}  # {coach_seat: ever_occupied}
    
    # Parcourir toutes les dessertes
    for desserte in dessertes:
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                coach_number = voiture.get("numero")
                for place in voiture.get("places", []):
                    seat_number = place.get("numero")
                    seat_id = f"{coach_number}_{seat_number}"
                    
                    # Initialiser à False si non existant
                    if seat_id not in all_seats:
                        all_seats[seat_id] = False
                    
                    # Si occupé à un moment quelconque, marquer comme occupé
                    occupation = place.get("occupation", {})
                    statut = occupation.get("statut")
                    if statut == "OCCUPE":
                        all_seats[seat_id] = True
    
    # Calculer le taux d'occupation
    total_seats = len(all_seats)
    occupied_seats = sum(1 for ever_occupied in all_seats.values() if ever_occupied)
    
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

def api_taux_occupation_siege(request, numero_train_commercial, numero_voiture, numero_siege, date_debut_mission):
    """
    API pour récupérer le taux d'occupation d'un siège spécifique
    
    URL: /API/tauxOccupationSiege/<numero_train_commercial>&<numero_voiture>&<numero_siege>&<date_debut_mission>
    
    Returns:
        JsonResponse: Taux d'occupation du siège sur l'ensemble des dessertes
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    
    train_data = load_json_file(train_file)
    
    if not train_data:
        return JsonResponse({"error": "Aucune donnée d'occupation des places disponible"}, status=404)
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Variables pour suivre l'occupation
    total_dessertes = len(dessertes)
    occupied_dessertes = 0
    occupation_details = []
    
    # Parcourir toutes les dessertes
    for desserte in dessertes:
        desserte_code_uic = desserte.get("codeUIC")
        desserte_rang = desserte.get("rang")
        is_occupied = False
        
        # Chercher le siège dans cette desserte
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                if voiture.get("numero") == numero_voiture:
                    for place in voiture.get("places", []):
                        if place.get("numero") == numero_siege:
                            occupation = place.get("occupation", {})
                            statut = occupation.get("statut")
                            is_occupied = (statut == "OCCUPE")
        
        # Ajouter les informations pour cette desserte
        occupation_details.append({
            "desserte_rang": desserte_rang,
            "desserte_code_uic": desserte_code_uic,
            "occupied": is_occupied
        })
        
        if is_occupied:
            occupied_dessertes += 1
    
    # Calculer le taux d'occupation
    occupation_rate = 0
    if total_dessertes > 0:
        occupation_rate = (occupied_dessertes / total_dessertes) * 100
    
    result = {
        "train_number": numero_train_commercial,
        "journey_date": date_debut_mission,
        "coach_number": numero_voiture,
        "seat_number": numero_siege,
        "total_dessertes": total_dessertes,
        "occupied_dessertes": occupied_dessertes,
        "occupation_rate": round(occupation_rate, 2),
        "occupation_details": occupation_details
    }
    
    return JsonResponse(result)

def api_taux_occupation_voiture(request, numero_train_commercial, numero_voiture, date_debut_mission):
    """
    API pour récupérer le taux d'occupation d'une voiture spécifique
    
    URL: /API/tauxOccupationVoiture/<numero_train_commercial>&<numero_voiture>&<date_debut_mission>
    
    Returns:
        JsonResponse: Taux d'occupation de la voiture
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    
    train_data = load_json_file(train_file)
    
    if not train_data:
        return JsonResponse({"error": "Aucune donnée d'occupation des places disponible"}, status=404)
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Dictionnaire pour suivre l'occupation de chaque siège de la voiture sur tout le trajet
    coach_seats = {}  # {seat_number: ever_occupied}
    
    # Parcourir toutes les dessertes
    for desserte in dessertes:
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                if voiture.get("numero") == numero_voiture:
                    for place in voiture.get("places", []):
                        seat_number = place.get("numero")
                        
                        # Initialiser à False si non existant
                        if seat_number not in coach_seats:
                            coach_seats[seat_number] = False
                        
                        # Si occupé à un moment quelconque, marquer comme occupé
                        occupation = place.get("occupation", {})
                        statut = occupation.get("statut")
                        if statut == "OCCUPE":
                            coach_seats[seat_number] = True
    
    # Calculer le taux d'occupation
    total_seats = len(coach_seats)
    occupied_seats = sum(1 for ever_occupied in coach_seats.values() if ever_occupied)
    
    occupation_rate = 0
    if total_seats > 0:
        occupation_rate = (occupied_seats / total_seats) * 100
    
    # Calculer également le taux d'occupation par desserte
    desserte_occupation = []
    
    for desserte in dessertes:
        desserte_code_uic = desserte.get("codeUIC")
        desserte_rang = desserte.get("rang")
        occupied_in_desserte = 0
        total_in_desserte = 0
        
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                if voiture.get("numero") == numero_voiture:
                    for place in voiture.get("places", []):
                        total_in_desserte += 1
                        occupation = place.get("occupation", {})
                        statut = occupation.get("statut")
                        if statut == "OCCUPE":
                            occupied_in_desserte += 1
        
        desserte_rate = 0
        if total_in_desserte > 0:
            desserte_rate = (occupied_in_desserte / total_in_desserte) * 100
        
        desserte_occupation.append({
            "desserte_rang": desserte_rang,
            "desserte_code_uic": desserte_code_uic,
            "total_seats": total_in_desserte,
            "occupied_seats": occupied_in_desserte,
            "occupation_rate": round(desserte_rate, 2)
        })
    
    result = {
        "train_number": numero_train_commercial,
        "journey_date": date_debut_mission,
        "coach_number": numero_voiture,
        "total_seats": total_seats,
        "occupied_seats": occupied_seats,
        "occupation_rate": round(occupation_rate, 2),
        "desserte_occupation": desserte_occupation
    }
    
    return JsonResponse(result)

def api_taux_occupation_desserte(request, numero_train_commercial, date_debut_mission):
    """
    API pour récupérer le taux d'occupation à chaque desserte
    
    URL: /API/tauxOccupationDesserte/<numero_train_commercial>&<date_debut_mission>
    
    Returns:
        JsonResponse: Taux d'occupation pour chaque desserte
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    stations_file = f"{data_folder}Référentiel_stations.json"
    
    train_data = load_json_file(train_file)
    stations_data = load_json_file(stations_file)
    
    if not train_data:
        return JsonResponse({"error": "Aucune donnée d'occupation des places disponible"}, status=404)
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Tableau pour stocker les informations d'occupation par desserte
    desserte_occupation = []
    
    for desserte in dessertes:
        desserte_code_uic = desserte.get("codeUIC")
        desserte_rang = desserte.get("rang")
        station_name = get_station_name(desserte_code_uic, stations_data)
        
        occupied_seats = 0
        total_seats = 0
        coach_occupation = {}  # {coach_number: {total: X, occupied: Y}}
        
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                coach_number = voiture.get("numero")
                
                if coach_number not in coach_occupation:
                    coach_occupation[coach_number] = {"total": 0, "occupied": 0}
                
                for place in voiture.get("places", []):
                    total_seats += 1
                    coach_occupation[coach_number]["total"] += 1
                    
                    occupation = place.get("occupation", {})
                    statut = occupation.get("statut")
                    
                    if statut == "OCCUPE":
                        occupied_seats += 1
                        coach_occupation[coach_number]["occupied"] += 1
        
        # Calculer le taux d'occupation pour cette desserte
        desserte_rate = 0
        if total_seats > 0:
            desserte_rate = (occupied_seats / total_seats) * 100
        
        # Calculer le taux d'occupation par voiture
        coach_stats = []
        for coach, stats in coach_occupation.items():
            coach_rate = 0
            if stats["total"] > 0:
                coach_rate = (stats["occupied"] / stats["total"]) * 100
            
            coach_stats.append({
                "coach_number": coach,
                "total_seats": stats["total"],
                "occupied_seats": stats["occupied"],
                "occupation_rate": round(coach_rate, 2)
            })
        
        desserte_occupation.append({
            "desserte_rang": desserte_rang,
            "desserte_code_uic": desserte_code_uic,
            "station_name": station_name,
            "total_seats": total_seats,
            "occupied_seats": occupied_seats,
            "occupation_rate": round(desserte_rate, 2),
            "coach_occupation": coach_stats
        })
    
    result = {
        "train_number": numero_train_commercial,
        "journey_date": date_debut_mission,
        "desserte_occupation": desserte_occupation
    }
    
    return JsonResponse(result)

def api_export_csv(request, numero_train_commercial, date_debut_mission):
    """
    API pour exporter les données d'occupation au format CSV
    
    URL: /API/exportCSV/<numero_train_commercial>&<date_debut_mission>
    
    Returns:
        FileResponse: Fichier CSV des données d'occupation
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    stations_file = f"{data_folder}Référentiel_stations.json"
    
    train_data = load_json_file(train_file)
    stations_data = load_json_file(stations_file)
    
    if not train_data:
        return HttpResponse("Aucune donnée d'occupation des places disponible", content_type='text/plain; charset=utf-8', status=404)
    
    # Créer un buffer pour stocker le CSV
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer)
    
    # Écrire l'en-tête
    csv_writer.writerow([
        "DessertRang", "DesserteCodeUIC", "StationName", 
        "Voiture", "Siege", "Statut", "FluxMontant", "FluxDescendant"
    ])
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Écrire les données
    for desserte in dessertes:
        desserte_code_uic = desserte.get("codeUIC")
        desserte_rang = desserte.get("rang")
        station_name = get_station_name(desserte_code_uic, stations_data)
        
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                coach_number = voiture.get("numero")
                for place in voiture.get("places", []):
                    seat_number = place.get("numero")
                    occupation = place.get("occupation", {})
                    statut = occupation.get("statut", "LIBRE")
                    flux_montant = "True" if occupation.get("fluxMontant", False) else "False"
                    flux_descendant = "True" if occupation.get("fluxDescendant", False) else "False"
                    
                    csv_writer.writerow([
                        desserte_rang, desserte_code_uic, station_name,
                        coach_number, seat_number, statut, flux_montant, flux_descendant
                    ])
    
    # Créer la réponse avec le fichier CSV
    response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{numero_train_commercial}_{date_debut_mission}.csv"'
    
    return response

def api_taux_occupation_desserte_specifique(request, numero_train_commercial, code_uic_desserte, date_debut_mission):
    """
    API pour récupérer le taux d'occupation pour une desserte spécifique
    
    URL: /API/tauxOccupationDesserteSpecifique/<numero_train_commercial>&<code_uic_desserte>&<date_debut_mission>
    
    Returns:
        JsonResponse: Taux d'occupation détaillé pour la desserte spécifiée
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    stations_file = f"{data_folder}Référentiel_stations.json"
    
    train_data = load_json_file(train_file)
    stations_data = load_json_file(stations_file)
    
    if not train_data or not stations_data:
        return JsonResponse({"error": "Aucune donnée d'occupation des places disponible"}, status=404)
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Trouver la desserte spécifique
    target_desserte = None
    for desserte in dessertes:
        if desserte.get("codeUIC") == code_uic_desserte:
            target_desserte = desserte
            break
    
    if not target_desserte:
        return JsonResponse({"error": f"Aucune desserte trouvée avec le code UIC {code_uic_desserte}"}, status=404)
    
    # Récupérer le nom de la station
    station_name = get_station_name(code_uic_desserte, stations_data)
    
    # Calculer le taux d'occupation pour cette desserte
    occupied_seats = 0
    total_seats = 0
    coach_occupation = {}  # {coach_number: {total: X, occupied: Y}}
    seat_details = []  # Liste détaillée de chaque siège
    
    for rame in target_desserte.get("rames", []):
        for voiture in rame.get("voitures", []):
            coach_number = voiture.get("numero")
            
            if coach_number not in coach_occupation:
                coach_occupation[coach_number] = {"total": 0, "occupied": 0}
            
            for place in voiture.get("places", []):
                seat_number = place.get("numero")
                total_seats += 1
                coach_occupation[coach_number]["total"] += 1
                
                occupation = place.get("occupation", {})
                statut = occupation.get("statut")
                flux_montant = occupation.get("fluxMontant", False)
                flux_descendant = occupation.get("fluxDescendant", False)
                
                is_occupied = (statut == "OCCUPE")
                
                if is_occupied:
                    occupied_seats += 1
                    coach_occupation[coach_number]["occupied"] += 1
                
                # Ajouter les détails du siège
                seat_details.append({
                    "coach": coach_number,
                    "seat": seat_number,
                    "status": statut,
                    "flux_montant": flux_montant,
                    "flux_descendant": flux_descendant
                })
    
    # Calculer le taux d'occupation
    desserte_rate = 0
    if total_seats > 0:
        desserte_rate = (occupied_seats / total_seats) * 100
    
    # Calculer le taux d'occupation par voiture
    coach_stats = []
    for coach, stats in coach_occupation.items():
        coach_rate = 0
        if stats["total"] > 0:
            coach_rate = (stats["occupied"] / stats["total"]) * 100
        
        coach_stats.append({
            "coach_number": coach,
            "total_seats": stats["total"],
            "occupied_seats": stats["occupied"],
            "occupation_rate": round(coach_rate, 2)
        })
    
    result = {
        "train_number": numero_train_commercial,
        "journey_date": date_debut_mission,
        "desserte": {
            "code_uic": code_uic_desserte,
            "station_name": station_name,
            "rang": target_desserte.get("rang"),
            "total_seats": total_seats,
            "occupied_seats": occupied_seats,
            "occupation_rate": round(desserte_rate, 2)
        },
        "coach_occupation": coach_stats,
        "seat_details": seat_details
    }
    
    return JsonResponse(result)