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
