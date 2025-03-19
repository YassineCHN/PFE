import tempfile
import shutil
import json
import os
def load_json_file(file_path):
    """
    Charge un fichier JSON depuis le chemin spécifié
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"Erreur lors du chargement du fichier {file_path}: {e}")
        return None

def get_station_name(code_uic, stations_data):
    """
    Récupère le nom court de la gare à partir du code UIC
    """
    for station in stations_data:
        if station['codeUIC'] == code_uic:
            return station['shortLabel']
    return code_uic  # Retourne le code UIC si non trouvé


def normalize_json_file(file_path):
    """
    Normalise un fichier JSON en convertissant un format avec objets par ligne en un tableau JSON standard.
    Si le fichier est déjà au format tableau JSON standard, il n'est pas modifié.
    
    Args:
        file_path (str): Chemin vers le fichier JSON à normaliser
        
    Returns:
        bool: True si le fichier a été normalisé ou était déjà au bon format, False en cas d'erreur
    """
    try:
        # Vérifier si le fichier existe
        if not os.path.isfile(file_path):
            print(f"Erreur: Le fichier {file_path} n'existe pas.")
            return False
        
        # Lire le contenu du fichier
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        
        # Si le contenu commence par '[', c'est déjà un tableau JSON standard
        if content.startswith('[') and content.endswith(']'):
            # Essayer de charger le JSON pour vérifier qu'il est valide
            try:
                json.loads(content)
                print(f"Le fichier {file_path} est déjà au format tableau JSON standard.")
                return True
            except json.JSONDecodeError:
                # JSON invalide, continuer avec la normalisation
                pass
        
        # Liste pour stocker les objets
        objects = []
        
        # Lire le contenu ligne par ligne
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line:  # Ignorer les lignes vides
                    continue
                
                try:
                    # Parser la ligne comme JSON
                    obj = json.loads(line)
                    objects.append(obj)
                except json.JSONDecodeError as e:
                    print(f"Ligne ignorée (JSON invalide): {line}")
                    print(f"Erreur: {e}")
        
        # Si aucun objet n'a été trouvé, c'est une erreur
        if not objects:
            print(f"Erreur: Aucun objet JSON valide trouvé dans le fichier {file_path}.")
            return False
        
        # Créer un fichier temporaire pour la sortie
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as temp_file:
            # Écrire dans le fichier temporaire au format JSON standard
            json.dump(objects, temp_file, ensure_ascii=False, indent=2)
            temp_file_path = temp_file.name
        
        # Remplacer le fichier original par le fichier temporaire
        shutil.move(temp_file_path, file_path)
        
        print(f"Normalisation du fichier {file_path} terminée.")
        print(f"Nombre d'objets traités: {len(objects)}")
        return True
    
    except Exception as e:
        print(f"Erreur lors de la normalisation du fichier {file_path}: {e}")
        return False