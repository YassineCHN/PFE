from django.http import HttpResponse
from common_utils.utils.json_utils import load_json_file, get_station_name
from pfeAPItest import settings
import os
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
        return HttpResponse("Aucune donnée d'occupation des places disponible", content_type='text/plain; charset=utf-8')
    
    # Récupérer toutes les dessertes triées par rang
    dessertes = sorted(train_data.get("dessertes", []), key=lambda x: int(x.get("rang", 0)))
    
    # Trouver la desserte actuelle et son rang
    current_desserte = None
    current_rang = -1
    current_index = -1
    
    for i, desserte in enumerate(dessertes):
        if desserte.get("codeUIC") == station_id:
            current_desserte = desserte
            current_rang = int(desserte.get("rang", 0))
            current_index = i
            break
    
    if not current_desserte:
        return HttpResponse(f"Aucune desserte trouvée pour la gare {station_id}", content_type='text/plain; charset=utf-8')
    
    # Vérifier s'il y a des dessertes futures
    if current_index >= len(dessertes) - 1:
        return HttpResponse("Fin du trajet, aucune desserte future", content_type='text/plain; charset=utf-8')
    
    # Diviser les dessertes en passées, actuelle et futures pour simplifier les recherches
    past_dessertes = dessertes[:current_index]
    future_dessertes = dessertes[current_index+1:]
    
    # Dictionnaire pour stocker les segments d'occupation à renvoyer
    seat_segments = {}
    
    # Parcourir tous les sièges dans la desserte actuelle
    for rame in current_desserte.get("rames", []):
        for voiture in rame.get("voitures", []):
            coach_number = voiture.get("numero")
            
            for place in voiture.get("places", []):
                seat_number = place.get("numero")
                seat_id = f"{coach_number}_{seat_number}"
                
                # Obtenir le statut actuel et les indicateurs de flux
                occupation = place.get("occupation", {})
                current_statut = occupation.get("statut", "LIBRE")
                current_flux_montant = occupation.get("fluxMontant", False)
                current_flux_descendant = occupation.get("fluxDescendant", False)
                
                # Cas 1: Siège LIBRE à la desserte actuelle
                if current_statut == "LIBRE":
                    # Trouver la prochaine occupation (prochain fluxMontant)
                    begin_station = None
                    begin_desserte_index = None
                    
                    for i, desserte in enumerate(future_dessertes):
                        for rame_f in desserte.get("rames", []):
                            for voiture_f in rame_f.get("voitures", []):
                                if voiture_f.get("numero") == coach_number:
                                    for place_f in voiture_f.get("places", []):
                                        if place_f.get("numero") == seat_number:
                                            occ_f = place_f.get("occupation", {})
                                            if occ_f.get("fluxMontant", False):
                                                begin_station = get_station_name(desserte.get("codeUIC"), stations_data)
                                                begin_desserte_index = current_index + 1 + i
                                                break
                                    if begin_station:
                                        break
                            if begin_station:
                                break
                        if begin_station:
                            break
                    
                    # Si on a trouvé une desserte de début, chercher la fin
                    if begin_station and begin_desserte_index is not None:
                        end_station = None
                        for desserte in dessertes[begin_desserte_index+1:]:
                            for rame_f in desserte.get("rames", []):
                                for voiture_f in rame_f.get("voitures", []):
                                    if voiture_f.get("numero") == coach_number:
                                        for place_f in voiture_f.get("places", []):
                                            if place_f.get("numero") == seat_number:
                                                occ_f = place_f.get("occupation", {})
                                                if occ_f.get("fluxDescendant", False):
                                                    end_station = get_station_name(desserte.get("codeUIC"), stations_data)
                                                    break
                                        if end_station:
                                            break
                                if end_station:
                                    break
                            if end_station:
                                break
                        
                        # Si segment complet trouvé, l'ajouter au résultat
                        if end_station:
                            seat_segments[seat_id] = {
                                "coach": coach_number,
                                "seat": seat_number,
                                "begin_station": begin_station,
                                "end_station": end_station
                            }
                
                # Cas 2: Siège OCCUPÉ avec changement de voyageur (montée et descente à la même gare)
                elif current_statut == "OCCUPE" and current_flux_montant and current_flux_descendant:
                    begin_station = get_station_name(station_id, stations_data)
                    end_station = None
                    
                    # Chercher la desserte de fin d'occupation (prochain fluxDescendant)
                    for desserte in future_dessertes:
                        for rame_f in desserte.get("rames", []):
                            for voiture_f in rame_f.get("voitures", []):
                                if voiture_f.get("numero") == coach_number:
                                    for place_f in voiture_f.get("places", []):
                                        if place_f.get("numero") == seat_number:
                                            occ_f = place_f.get("occupation", {})
                                            if occ_f.get("fluxDescendant", False):
                                                end_station = get_station_name(desserte.get("codeUIC"), stations_data)
                                                break
                                    if end_station:
                                        break
                            if end_station:
                                break
                        if end_station:
                            break
                    
                    # Si on a trouvé une fin, ajouter le segment
                    if end_station:
                        seat_segments[seat_id] = {
                            "coach": coach_number,
                            "seat": seat_number,
                            "begin_station": begin_station,
                            "end_station": end_station
                        }
                
                # Cas 3: Siège OCCUPÉ sans changement à cette desserte
                elif current_statut == "OCCUPE":
                    # Chercher la desserte de début d'occupation (précédent fluxMontant)
                    begin_station = None
                    
                    # Parcourir les dessertes passées en sens inverse pour trouver la plus récente montée
                    for desserte in reversed(past_dessertes + [current_desserte]):
                        for rame_p in desserte.get("rames", []):
                            for voiture_p in rame_p.get("voitures", []):
                                if voiture_p.get("numero") == coach_number:
                                    for place_p in voiture_p.get("places", []):
                                        if place_p.get("numero") == seat_number:
                                            occ_p = place_p.get("occupation", {})
                                            if occ_p.get("fluxMontant", False):
                                                begin_station = get_station_name(desserte.get("codeUIC"), stations_data)
                                                break
                                    if begin_station:
                                        break
                            if begin_station:
                                break
                        if begin_station:
                            break
                    
                    # Si on n'a pas trouvé de début mais que le siège est occupé, 
                    # c'est que le voyageur est monté avant la première desserte du train
                    if not begin_station:
                        begin_station = get_station_name(dessertes[0].get("codeUIC"), stations_data)
                    
                    # Chercher la desserte de fin d'occupation (prochain fluxDescendant)
                    end_station = None
                    # Si le voyageur descend à cette desserte, on ne l'inclut pas
                    if not current_flux_descendant:
                        for desserte in future_dessertes:
                            for rame_f in desserte.get("rames", []):
                                for voiture_f in rame_f.get("voitures", []):
                                    if voiture_f.get("numero") == coach_number:
                                        for place_f in voiture_f.get("places", []):
                                            if place_f.get("numero") == seat_number:
                                                occ_f = place_f.get("occupation", {})
                                                if occ_f.get("fluxDescendant", False):
                                                    end_station = get_station_name(desserte.get("codeUIC"), stations_data)
                                                    break
                                        if end_station:
                                            break
                                if end_station:
                                    break
                            if end_station:
                                break
                    else:
                        # Le voyageur descend à cette desserte, on ne l'inclut pas
                        continue
                    
                    # Si on n'a pas trouvé de fin, c'est que le voyageur descend à la dernière desserte
                    if not end_station:
                        end_station = get_station_name(dessertes[-1].get("codeUIC"), stations_data)
                    
                    # Ajouter le segment au résultat
                    seat_segments[seat_id] = {
                        "coach": coach_number,
                        "seat": seat_number,
                        "begin_station": begin_station,
                        "end_station": end_station
                    }
    
    # Formater la réponse selon le cahier des charges
    response_text = ""
    
    for seat_id, segment in seat_segments.items():
        coach = segment["coach"]
        seat = segment["seat"]
        begin_station = segment["begin_station"]
        end_station = segment["end_station"]
        
        response_text += f"seat.coach = {coach}\n"
        response_text += f"seat.idSeat = {seat}\n"
        response_text += f"seat.beginStation = {begin_station}\n"
        response_text += f"seat.endStation = {end_station}\n"
    
    if not response_text:
        response_text = "Aucune occupation future des places disponible pour cette gare"
    
    return HttpResponse(response_text, content_type='text/plain; charset=utf-8')
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
