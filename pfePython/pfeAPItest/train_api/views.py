import os
import json
import tempfile
from django.shortcuts import render, redirect
from django.http import HttpResponse,JsonResponse
from django.conf import settings
from .api import get_seat_occupation
from .utils.json_utils import normalize_json_file, load_json_file
def index(request):
    """
    Vue d'accueil pour l'application
    """
    return HttpResponse("API d'occupation des places de train SNCF")

def controleur_form(request):
    """
    Vue pour afficher le formulaire de recherche d'occupation de siège par le contrôleur
    """
    return render(request, 'train_api/controleur_form.html')
def gestionnaire_form(request):
    """
    Vue pour afficher le formulaire du gestionnaire pour les taux d'occupation
    """
    return render(request, 'train_api/gestionnaire_form.html')
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
        
        return render(request, 'train_api/controleur_result.html', context)
    
    # Redirection vers le formulaire en cas d'accès direct à cette URL
    return redirect('controleur_form')


def normalize_json_page(request):
    """
    Affiche et traite la page pour normaliser un fichier JSON et modifier des enregistrements
    """
    context = {}
    
    if request.method == 'POST':
        # comme en java on un paramètre caché/hidden dans le form
        action = request.POST.get('action', '')
        
        # Traitement de la normalisation du fichier
        if action == 'normalize' and 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            
            # Vérification de l'extension du fichier
            if not uploaded_file.name.lower().endswith('.json'):
                context['error'] = 'Le fichier doit être au format JSON.'
                return render(request, 'train_api/normalize_json.html', context)
            
            # Chemin du fichier dans le dossier data
            data_folder = os.path.join(settings.BASE_DIR, 'data')
            
            # Si le dossier n'existe pas, le créer
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)
            
            # Définir le chemin de destination
            destination_path = os.path.join(data_folder, 'Référentiel_stations.json')
            
            try:
                # Créer un fichier temporaire pour stocker le fichier uploadé
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    # Écrire le contenu du fichier uploadé dans le fichier temporaire
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)
                    
                    temp_file_path = temp_file.name
                
                # Vérifier le format du fichier original
                original_format = "Unknown"
                objects_count = 0
                
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    
                    # Déterminer le format original
                    if content.startswith('[') and content.endswith(']'):
                        try:
                            data = json.loads(content)
                            objects_count = len(data)
                            original_format = "Tableau JSON"
                        except json.JSONDecodeError:
                            original_format = "JSON mal formé"
                            # Tenter de compter les objets ligne par ligne
                            with open(temp_file_path, 'r', encoding='utf-8') as f2:
                                for line in f2:
                                    line = line.strip()
                                    if line and not line.startswith('[') and not line.startswith(']'):
                                        objects_count += 1
                    else:
                        # Compter les objets JSON par ligne
                        original_format = "Objets JSON par ligne"
                        with open(temp_file_path, 'r', encoding='utf-8') as f2:
                            for line in f2:
                                line = line.strip()
                                if line:
                                    objects_count += 1
                
                # Normaliser le fichier temporaire
                if not normalize_json_file(temp_file_path):
                    os.unlink(temp_file_path)
                    context['error'] = 'Erreur lors de la normalisation du fichier.'
                    return render(request, 'train_api/normalize_json.html', context)
                
                # Copier le fichier normalisé vers la destination finale
                with open(temp_file_path, 'rb') as src_file:
                    with open(destination_path, 'wb') as dst_file:
                        dst_file.write(src_file.read())
                
                # Supprimer le fichier temporaire
                os.unlink(temp_file_path)
                
                # Obtenir la taille finale du fichier
                final_size = os.path.getsize(destination_path)
                
                context['success'] = True
                context['success_message'] = 'Le fichier a été normalisé avec succès.'
                context['objects_count'] = objects_count
                context['original_format'] = original_format
                context['final_size'] = format_size(final_size)
                
            except Exception as e:
                # En cas d'erreur, supprimer le fichier temporaire s'il existe
                if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
                context['error'] = f'Une erreur est survenue lors du traitement du fichier: {str(e)}'
        
        # Traitement de la modification d'un enregistrement
        elif action == 'edit':
            uic_code = request.POST.get('uic_code', '')
            label = request.POST.get('label', '')
            short_label = request.POST.get('short_label', '')
            long_label = request.POST.get('long_label', '')
            
            if not uic_code or not label or not short_label or not long_label:
                context['error'] = 'Tous les champs sont obligatoires.'
                return render(request, 'train_api/normalize_json.html', context)
            
            try:
                # Chemin du fichier dans le dossier data
                data_folder = os.path.join(settings.BASE_DIR, 'data')
                stations_file = os.path.join(data_folder, 'Référentiel_stations.json')
                
                # Charger les données du fichier
                stations_data = load_json_file(stations_file)
                
                if not stations_data:
                    context['error'] = 'Impossible de charger le fichier de référentiel des gares.'
                    return render(request, 'train_api/normalize_json.html', context)
                
                # Rechercher la gare à modifier
                station_found = False
                for i, station in enumerate(stations_data):
                    if station.get('codeUIC') == uic_code:
                        # Mettre à jour les informations
                        stations_data[i]['label'] = label
                        stations_data[i]['shortLabel'] = short_label
                        stations_data[i]['longLabel'] = long_label
                        station_found = True
                        break
                
                if not station_found:
                    context['error'] = f'Aucune gare trouvée avec le code UIC: {uic_code}'
                    return render(request, 'train_api/normalize_json.html', context)
                
                # Enregistrer les données mises à jour
                with open(stations_file, 'w', encoding='utf-8') as f:
                    json.dump(stations_data, f, ensure_ascii=False, indent=2)
                
                context['success'] = True
                context['success_message'] = f'Les informations de la gare avec le code UIC {uic_code} ont été mises à jour avec succès.'
                
            except Exception as e:
                context['error'] = f'Une erreur est survenue lors de la mise à jour des informations: {str(e)}'
    
    return render(request, 'train_api/normalize_json.html', context)
def find_station(request, uic_code):
    """
    API pour rechercher une gare par son code UIC
    """
    try:
        # Chemin du fichier dans le dossier data
        data_folder = os.path.join(settings.BASE_DIR, 'data')
        stations_file = os.path.join(data_folder, 'Référentiel_stations.json')
        
        # Charger les données du fichier
        stations_data = load_json_file(stations_file)
        
        if not stations_data:
            return JsonResponse({'error': 'Impossible de charger le fichier de référentiel des gares.'}, status=500)
        
        # Rechercher la gare
        for station in stations_data:
            if station.get('codeUIC') == uic_code:
                return JsonResponse(station)
        
        # Si aucune gare n'est trouvée
        return JsonResponse({'error': 'Gare non trouvée'}, status=404)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
def format_size(size_bytes):
    """
    Formate une taille en bytes en une chaîne lisible
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"