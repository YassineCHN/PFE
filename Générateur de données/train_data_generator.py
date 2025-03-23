import json
import random
import datetime
import os
from typing import List, Dict, Any, Optional, Tuple

def generate_train_data(
    train_number: str,
    date: str,
    stations: List[Dict[str, str]],
    num_coaches: int = 8,
    seats_per_coach: int = 10,
    occupation_rate: float = 0.3,
    output_folder: Optional[str] = None
) -> Dict[str, Any]:
    """
    Génère un jeu de données d'occupation d'un train au format JSON.
    
    Args:
        train_number (str): Numéro du train
        date (str): Date au format YYYY-MM-DD
        stations (List[Dict]): Liste des gares (avec codeUIC, shortLabel, etc.)
        num_coaches (int): Nombre de voitures
        seats_per_coach (int): Nombre de sièges par voiture
        occupation_rate (float): Taux d'occupation global souhaité (0-1)
        output_folder (str, optional): Dossier de sortie pour le fichier JSON
    
    Returns:
        Dict[str, Any]: Données générées au format attendu par l'application
    """
    # Sélectionner un sous-ensemble de gares pour le parcours du train
    selected_stations = random.sample(stations, min(len(stations), random.randint(7, 12)))
    
    # Trier les gares pour créer un parcours logique
    selected_stations_with_rank = [(station, i) for i, station in enumerate(selected_stations)]
    
    # Créer la structure de base du document
    train_data = {
        "circulation": {
            "numero": train_number,
            "date": date,
            "codeOperateur": "1187",
            "typeMode": "FERRE"
        },
        "dessertes": []
    }
    
    # Liste pour suivre l'occupation de chaque siège tout au long du trajet
    seat_occupations = {}  # {(coach, seat): [(start_rang, end_rang), ...]}
    
    # Générer les dessertes (gares)
    for rank, (station, i) in enumerate(selected_stations_with_rank):
        desserte = {
            "codeUIC": station["codeUIC"],
            "rang": str(rank),
            "rames": [{
                "voitures": []
            }]
        }
        
        # Générer les voitures et sièges
        for coach in range(1, num_coaches + 1):
            voiture = {
                "numero": str(coach),
                "places": []
            }
            
            # Générer les sièges pour cette voiture
            for seat in range(1, seats_per_coach + 1):
                seat_id = (coach, seat)
                
                # Déterminer le statut d'occupation pour ce siège à cette desserte
                if seat_id not in seat_occupations:
                    seat_occupations[seat_id] = []
                
                # Déterminer si c'est un siège de première ou seconde classe
                classe = "PREMIERE" if coach <= (num_coaches // 3) else "SECONDE"
                
                # Déterminer le compartiment et le niveau
                compartiment = "1" if seat <= seats_per_coach // 2 else "2"
                niveau = "SALLE_BASSE" if seat % 2 == 1 else "SALLE_HAUTE"
                
                # Créer le siège de base avec occupation LIBRE par défaut
                place = {
                    "numero": str(seat),
                    "classe": classe,
                    "compartiment": compartiment,
                    "niveau": niveau,
                    "type": "PLACE_ASSISE",
                    "occupation": {
                        "statut": "LIBRE"
                    }
                }
                
                # Vérifier si le siège est déjà occupé par un segment existant
                is_occupied = False
                for start_rang, end_rang in seat_occupations[seat_id]:
                    if start_rang <= rank <= end_rang:
                        is_occupied = True
                        break
                
                # Si le siège n'est pas occupé, déterminer s'il doit être occupé à partir de cette gare
                if not is_occupied and rank < len(selected_stations_with_rank) - 1:
                    # Probabilité d'occupation plus élevée pour les premières classes et début du trajet
                    base_probability = occupation_rate
                    if classe == "PREMIERE":
                        base_probability *= 1.5
                    if rank < len(selected_stations_with_rank) // 3:
                        base_probability *= 1.3
                    
                    if random.random() < base_probability:
                        # Décider où le passager descendra
                        end_desserte_rank = random.randint(
                            rank + 1, min(len(selected_stations_with_rank) - 1, rank + 5)
                        )
                        
                        # Enregistrer l'occupation
                        seat_occupations[seat_id].append((rank, end_desserte_rank))
                        
                        # Marquer comme occupé avec fluxMontant
                        place["occupation"]["statut"] = "OCCUPE"
                        place["occupation"]["fluxMontant"] = True
                
                # Vérifier si un passager descend à cette desserte
                for start_rang, end_rang in seat_occupations[seat_id]:
                    if end_rang == rank:
                        place["occupation"]["fluxDescendant"] = True
                
                # Possibilité d'avoir un changement de voyageur (descente et montée à la même desserte)
                if (rank > 0 and rank < len(selected_stations_with_rank) - 1 and 
                    "fluxDescendant" in place["occupation"] and 
                    random.random() < 0.2):
                    
                    # Décider où le nouveau passager descendra
                    end_desserte_rank = random.randint(
                        rank + 1, min(len(selected_stations_with_rank) - 1, rank + 5)
                    )
                    
                    # Enregistrer l'occupation
                    seat_occupations[seat_id].append((rank, end_desserte_rank))
                    
                    # Marquer comme occupé avec fluxMontant et fluxDescendant
                    place["occupation"]["statut"] = "OCCUPE"
                    place["occupation"]["fluxMontant"] = True
                
                voiture["places"].append(place)
            
            desserte["rames"][0]["voitures"].append(voiture)
        
        train_data["dessertes"].append(desserte)
    
    # Mettre à jour le statut d'occupation pour les dessertes intermédiaires
    for rank in range(len(train_data["dessertes"])):
        for coach in range(1, num_coaches + 1):
            for seat in range(1, seats_per_coach + 1):
                seat_id = (coach, seat)
                
                is_occupied = False
                for start_rang, end_rang in seat_occupations[seat_id]:
                    if start_rang <= rank <= end_rang:
                        is_occupied = True
                        break
                
                if is_occupied:
                    # Trouver ce siège dans la desserte actuelle
                    desserte = train_data["dessertes"][rank]
                    for voiture in desserte["rames"][0]["voitures"]:
                        if voiture["numero"] == str(coach):
                            for place in voiture["places"]:
                                if place["numero"] == str(seat):
                                    place["occupation"]["statut"] = "OCCUPE"
    
    # Écrire le fichier JSON si un dossier de sortie est spécifié
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        output_file = os.path.join(output_folder, f"{train_number}_{date}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(train_data, f, ensure_ascii=False, indent=2)
        print(f"Fichier JSON généré: {output_file}")
    
    return train_data

def generate_stations_data(num_stations: int = 30) -> List[Dict[str, str]]:
    """
    Génère des données de stations pour le référentiel des gares.
    
    Args:
        num_stations (int): Nombre de stations à générer
    
    Returns:
        List[Dict[str, str]]: Liste des stations générées
    """
    # Liste de villes
    cities = [
        "Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", 
        "Bordeaux", "Lille", "Rennes", "Reims", "Le Havre", "Toulon", "Grenoble", "Dijon",
        "Angers", "Nîmes", "Villeurbanne", "Tours", "Clermont-Ferrand", "Limoges", "Amiens",
        "Metz", "Besançon", "Caen", "Orléans", "Mulhouse", "Brest", "Perpignan", "Nancy",
        "Avignon", "Cannes", "La Rochelle", "Antibes", "Saint-Étienne", "Annecy", "Valence",
        "Lorient", "Chambéry", "Troyes", "Poitiers", "Aix-en-Provence", "Bayonne", "Saint-Malo"
    ]
    
    # Suffixes pour les noms de gares
    suffixes = [
        "Gare Centrale", "Gare de l'Est", "Gare du Nord", "Gare Saint-Jean", "Gare Part-Dieu",
        "Gare TGV", "Gare Montparnasse", "Gare d'Austerlitz", "Gare Maritime", "Gare Routière",
        "Gare des Brotteaux", "Gare de Lyon", "Gare Saint-Charles", "Gare Saint-Lazare", "Gare de l'Ouest"
    ]
    
    # Générer des données de stations aléatoires
    stations = []
    used_cities = set()
    
    for i in range(num_stations):
        # Choisir une ville qui n'a pas encore été utilisée si possible
        available_cities = [city for city in cities if city not in used_cities]
        if not available_cities:
            available_cities = cities
        
        city = random.choice(available_cities)
        used_cities.add(city)
        
        # Génération d'un code UIC unique à 8 chiffres commençant par 87
        code_uic = f"87{random.randint(100000, 999999)}"
        
        # Génération de noms de gare
        if random.random() < 0.7 and suffixes:  # 70% de chance d'avoir un suffixe
            suffix = random.choice(suffixes)
            label = f"{city} {suffix}"
        else:
            label = city
        
        # Version courte du nom
        if len(label) > 15:
            short_label = f"{city[:8]}.."
        else:
            short_label = city
        
        # Version longue du nom
        long_label = label
        if random.random() < 0.3:  # 30% de chance d'avoir des informations supplémentaires
            long_label += f" (Plateforme {random.randint(1, 5)})"
        
        # Ajouter la station à la liste
        stations.append({
            "codeUIC": code_uic,
            "label": label,
            "shortLabel": short_label,
            "longLabel": long_label
        })
    
    return stations

def generate_train_dataset(
    num_trains: int = 5,
    base_date: Optional[str] = None,
    output_folder: Optional[str] = "./data"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """
    Génère un ensemble complet de données pour plusieurs trains.
    
    Args:
        num_trains (int): Nombre de trains à générer
        base_date (str, optional): Date de départ au format YYYY-MM-DD (par défaut: date actuelle)
        output_folder (str, optional): Dossier de sortie pour les fichiers JSON
    
    Returns:
        Tuple[List[Dict], List[Dict]]: (données des trains, données des stations)
    """
    # Générer des stations
    stations = generate_stations_data(num_stations=30)
    
    # Écrire le fichier de référentiel des stations
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
        stations_file = os.path.join(output_folder, "Référentiel_stations.json")
        with open(stations_file, 'w', encoding='utf-8') as f:
            json.dump(stations, f, ensure_ascii=False, indent=2)
        print(f"Fichier de référentiel des stations généré: {stations_file}")
    
    # Date de base
    if base_date is None:
        base_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    base_date_obj = datetime.datetime.strptime(base_date, "%Y-%m-%d")
    
    # Générer des données pour chaque train
    train_data_list = []
    
    for i in range(num_trains):
        # Générer un numéro de train à 4 ou 5 chiffres
        train_number = str(random.randint(1000, 99999))
        
        # Date du train (jusqu'à 7 jours dans le futur)
        days_offset = random.randint(0, 7)
        train_date = (base_date_obj + datetime.timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        # Taux d'occupation variable
        occupation_rate = random.uniform(0.2, 0.8)
        
        # Générer les données du train
        train_data = generate_train_data(
            train_number=train_number,
            date=train_date,
            stations=stations,
            num_coaches=random.randint(5, 10),
            seats_per_coach=random.randint(8, 20),
            occupation_rate=occupation_rate,
            output_folder=output_folder
        )
        
        train_data_list.append(train_data)
    
    return train_data_list, stations

# Exemple d'utilisation dans un notebook Jupyter:
"""
# Importer le générateur de données
from train_data_generator import generate_train_dataset

# Générer un ensemble de données (5 trains)
train_data_list, stations = generate_train_dataset(
    num_trains=5,
    base_date="2025-03-20",
    output_folder="./data"
)

# Afficher les informations générées
print(f"Nombre de stations générées: {len(stations)}")
print(f"Nombre de trains générés: {len(train_data_list)}")

# Exemple d'accès aux données
train = train_data_list[0]
print(f"Train {train['circulation']['numero']}, Date: {train['circulation']['date']}")
print(f"Nombre de dessertes: {len(train['dessertes'])}")

# Pour charger les données générées
import json

with open("./data/Référentiel_stations.json", "r", encoding="utf-8") as f:
    stations = json.load(f)

# Pour charger un train spécifique
train_number = train_data_list[0]['circulation']['numero']
train_date = train_data_list[0]['circulation']['date']

with open(f"./data/{train_number}_{train_date}.json", "r", encoding="utf-8") as f:
    train_data = json.load(f)
"""