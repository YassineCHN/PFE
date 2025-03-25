
import os
import csv
from io import StringIO
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from common_utils.utils.json_utils import load_json_file, get_station_name

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

def api_taux_occupation_voiture_global(request, numero_train_commercial, date_debut_mission):
    """
    API pour récupérer le taux d'occupation moyen de chaque voiture sur l'ensemble du parcours
    
    URL: /API/tauxOccupationVoitureGlobal/<numero_train_commercial>&<date_debut_mission>
    
    Returns:
        JsonResponse: Taux d'occupation moyen par voiture sur tout le parcours
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    
    train_data = load_json_file(train_file)
    
    if not train_data:
        return JsonResponse({"error": "Aucune donnée d'occupation des places disponible"}, status=404)
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Structure pour collecter les données par voiture
    coaches_data = {}
    
    # Pour chaque desserte, calculer l'occupation par voiture
    for desserte in dessertes:
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                coach_number = voiture.get("numero")
                
                # Initialiser les données de cette voiture si nécessaire
                if coach_number not in coaches_data:
                    coaches_data[coach_number] = {
                        "desserte_rates": [],  # Taux par desserte
                        "total_seats": 0,      # Nombre de sièges dans la voiture
                    }
                
                # Compter les sièges et les sièges occupés pour cette desserte
                total_seats = len(voiture.get("places", []))
                occupied_seats = sum(1 for place in voiture.get("places", []) 
                                    if place.get("occupation", {}).get("statut") == "OCCUPE")
                
                # Mettre à jour le nombre total de sièges si non encore défini
                if coaches_data[coach_number]["total_seats"] == 0:
                    coaches_data[coach_number]["total_seats"] = total_seats
                
                # Calculer le taux d'occupation pour cette desserte
                desserte_rate = 0
                if total_seats > 0:
                    desserte_rate = (occupied_seats / total_seats) * 100
                
                # Ajouter ce taux à la liste des taux pour cette voiture
                coaches_data[coach_number]["desserte_rates"].append(desserte_rate)
    
    # Préparer les résultats
    coaches_result = []
    all_average_rates = []
    
    for coach_number, data in sorted(coaches_data.items(), key=lambda x: int(x[0])):
        # Calculer le taux moyen en faisant la moyenne des taux par desserte
        average_rate = 0
        if data["desserte_rates"]:
            average_rate = sum(data["desserte_rates"]) / len(data["desserte_rates"])
        
        # Compter les instances où cette voiture a été occupée au moins une fois
        times_occupied = sum(1 for rate in data["desserte_rates"] if rate > 0)
        
        coach_result = {
            "coach_number": coach_number,
            "average_occupation_rate": round(average_rate, 1),
            "total_seats": data["total_seats"],
            "times_occupied": times_occupied
        }
        
        coaches_result.append(coach_result)
        all_average_rates.append(average_rate)
    
    # Calculer la moyenne globale de toutes les voitures
    global_average = 0
    if all_average_rates:
        global_average = sum(all_average_rates) / len(all_average_rates)
    
    result = {
        "train_number": numero_train_commercial,
        "journey_date": date_debut_mission,
        "coaches": coaches_result,
        "global_average": round(global_average, 1)
    }
    
    return JsonResponse(result)

def api_passager_flow(request, numero_train_commercial, date_debut_mission):
    """
    API pour récupérer les données de flux de passagers (montées/descentes) pour un train
    
    URL: /API/fluxPassagers/<numero_train_commercial>&<date_debut_mission>
    
    Returns:
        JsonResponse: Données de flux de passagers par desserte
    """
    data_folder = os.path.join(settings.BASE_DIR, 'data/')
    train_file = f"{data_folder}{numero_train_commercial}_{date_debut_mission}.json"
    stations_file = f"{data_folder}Référentiel_stations.json"
    
    train_data = load_json_file(train_file)
    stations_data = load_json_file(stations_file)
    
    if not train_data or not stations_data:
        return JsonResponse({"error": "Aucune donnée disponible"}, status=404)
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Tableau pour stocker les données de flux
    flow_data = []
    
    for desserte in dessertes:
        desserte_code_uic = desserte.get("codeUIC")
        desserte_rang = desserte.get("rang")
        station_name = get_station_name(desserte_code_uic, stations_data)
        
        # Compteurs pour les montées et descentes
        boarding_count = 0
        alighting_count = 0
        
        for rame in desserte.get("rames", []):
            for voiture in rame.get("voitures", []):
                for place in voiture.get("places", []):
                    occupation = place.get("occupation", {})
                    flux_montant = occupation.get("fluxMontant", False)
                    flux_descendant = occupation.get("fluxDescendant", False)
                    
                    if flux_montant:
                        boarding_count += 1
                    
                    if flux_descendant:
                        alighting_count += 1
        
        flow_data.append({
            "desserte_rang": desserte_rang,
            "desserte_code_uic": desserte_code_uic,
            "station_name": station_name,
            "boarding": boarding_count,
            "alighting": alighting_count,
            "net_flow": boarding_count - alighting_count
        })
    
    result = {
        "train_number": numero_train_commercial,
        "journey_date": date_debut_mission,
        "flow_data": flow_data
    }
    
    return JsonResponse(result)


    return HttpResponse("API test successful")