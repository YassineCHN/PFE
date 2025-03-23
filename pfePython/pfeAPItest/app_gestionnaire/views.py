import tempfile
from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from django.conf import settings
import os, json
from common_utils.utils.json_utils import normalize_json_file, load_json_file

def gestionnaire_form(request):
    """
    Vue pour afficher le formulaire du gestionnaire pour les taux d'occupation
    """
    return render(request, 'app_gestionnaire/gestionnaire_form.html')

def dashboard(request):
    """
    Vue pour afficher le tableau de bord d'occupation des trains
    """
    return render(request, 'app_gestionnaire/dashboard.html')

def normalize_json_page(request):
    """
    Affiche et traite la page pour normaliser un fichier JSON et gérer les gares (ajout, modification, suppression)
    """
    context = {}
    
    if request.method == 'POST':
        # Récupérer l'action demandée
        action = request.POST.get('action', '')
        
        # Chemin du fichier dans le dossier data
        data_folder = os.path.join(settings.BASE_DIR, 'data')
        
        # Si le dossier n'existe pas, le créer
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        # Définir le chemin du fichier de référentiel
        stations_file = os.path.join(data_folder, 'Référentiel_stations.json')
        
        # Traitement de la normalisation du fichier
        if action == 'normalize' and 'file' in request.FILES:
            uploaded_file = request.FILES['file']
            
            # Vérification de l'extension du fichier
            if not uploaded_file.name.lower().endswith('.json'):
                context['error'] = 'Le fichier doit être au format JSON.'
                return render(request, 'app_gestionnaire/normalize_json.html', context)
            
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
                    return render(request, 'app_gestionnaire/normalize_json.html', context)
                
                # Copier le fichier normalisé vers la destination finale
                with open(temp_file_path, 'rb') as src_file:
                    with open(stations_file, 'wb') as dst_file:
                        dst_file.write(src_file.read())
                
                # Supprimer le fichier temporaire
                os.unlink(temp_file_path)
                
                
                
                context['success'] = True
                context['success_message'] = 'Le fichier a été normalisé avec succès.'
                context['objects_count'] = objects_count
                context['original_format'] = original_format
                
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
                return render(request, 'app_gestionnaire/normalize_json.html', context)
            
            try:
                # Charger les données du fichier
                stations_data = load_json_file(stations_file)
                
                if not stations_data:
                    context['error'] = 'Impossible de charger le fichier de référentiel des gares.'
                    return render(request, 'app_gestionnaire/normalize_json.html', context)
                
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
                    return render(request, 'app_gestionnaire/normalize_json.html', context)
                
                # Enregistrer les données mises à jour
                with open(stations_file, 'w', encoding='utf-8') as f:
                    json.dump(stations_data, f, ensure_ascii=False, indent=2)
                
                context['success'] = True
                context['success_message'] = f'Les informations de la gare avec le code UIC {uic_code} ont été mises à jour avec succès.'
                
            except Exception as e:
                context['error'] = f'Une erreur est survenue lors de la mise à jour des informations: {str(e)}'
        
        # Traitement de l'ajout d'une gare
        elif action == 'add':
            uic_code = request.POST.get('uic_code', '')
            label = request.POST.get('label', '')
            short_label = request.POST.get('short_label', '')
            long_label = request.POST.get('long_label', '')
            
            if not uic_code or not label or not short_label or not long_label:
                context['error'] = 'Tous les champs sont obligatoires.'
                return render(request, 'app_gestionnaire/normalize_json.html', context)
            
            try:
                # Charger les données du fichier
                stations_data = load_json_file(stations_file)
                
                if not stations_data:
                    # Si le fichier n'existe pas ou est vide, créer une nouvelle liste
                    stations_data = []
                
                # Vérifier si une gare avec ce code UIC existe déjà
                for station in stations_data:
                    if station.get('codeUIC') == uic_code:
                        context['error'] = f'Une gare avec le code UIC {uic_code} existe déjà.'
                        return render(request, 'app_gestionnaire/normalize_json.html', context)
                
                # Créer un nouveau dictionnaire pour la gare
                new_station = {
                    'codeUIC': uic_code,
                    'label': label,
                    'shortLabel': short_label,
                    'longLabel': long_label
                }
                
                # Ajouter la nouvelle gare à la liste
                stations_data.append(new_station)
                
                # Enregistrer les données mises à jour
                with open(stations_file, 'w', encoding='utf-8') as f:
                    json.dump(stations_data, f, ensure_ascii=False, indent=2)
                
                context['success'] = True
                context['success_message'] = f'La gare avec le code UIC {uic_code} a été ajoutée avec succès.'
                
            except Exception as e:
                context['error'] = f'Une erreur est survenue lors de l\'ajout de la gare: {str(e)}'
        
        # Traitement de la suppression d'une gare
        elif action == 'delete':
            uic_code = request.POST.get('uic_code', '')
            
            if not uic_code:
                context['error'] = 'Le code UIC est obligatoire.'
                return render(request, 'app_gestionnaire/normalize_json.html', context)
            
            try:
                # Charger les données du fichier
                stations_data = load_json_file(stations_file)
                
                if not stations_data:
                    context['error'] = 'Impossible de charger le fichier de référentiel des gares.'
                    return render(request, 'app_gestionnaire/normalize_json.html', context)
                
                # Rechercher la gare à supprimer
                initial_count = len(stations_data)
                stations_data = [station for station in stations_data if station.get('codeUIC') != uic_code]
                
                if len(stations_data) == initial_count:
                    context['error'] = f'Aucune gare trouvée avec le code UIC: {uic_code}'
                    return render(request, 'app_gestionnaire/normalize_json.html', context)
                
                # Enregistrer les données mises à jour
                with open(stations_file, 'w', encoding='utf-8') as f:
                    json.dump(stations_data, f, ensure_ascii=False, indent=2)
                
                context['success'] = True
                context['success_message'] = f'La gare avec le code UIC {uic_code} a été supprimée avec succès.'
                
            except Exception as e:
                context['error'] = f'Une erreur est survenue lors de la suppression de la gare: {str(e)}'
    
    return render(request, 'app_gestionnaire/normalize_json.html', context)
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