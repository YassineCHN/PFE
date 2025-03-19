import os
import json
import csv
import datetime
from typing import List, Dict, Any, Optional, Tuple
import glob
import pandas as pd

def consolidate_train_data_to_csv(
    input_folder: str,
    output_file: str,
    train_number: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    include_all_fields: bool = False,
    verbose: bool = True
) -> str:
    """
    Convertit tous les fichiers JSON de données de train dans un dossier en un seul fichier CSV.
    
    Args:
        input_folder: Dossier contenant les fichiers JSON de train
        output_file: Chemin du fichier CSV de sortie
        train_number: Filtrer sur un numéro de train spécifique (optionnel)
        start_date: Date de début au format YYYY-MM-DD (optionnel)
        end_date: Date de fin au format YYYY-MM-DD (optionnel)
        include_all_fields: Inclure tous les champs détaillés (sinon, résumé par jour/gare)
        verbose: Afficher la progression
    
    Returns:
        str: Chemin du fichier CSV généré
    """
    if verbose:
        print(f"Consolidation des données de train dans {input_folder}")
    
    # Déterminer le motif de recherche des fichiers
    if train_number:
        file_pattern = f"{train_number}_*.json"
    else:
        file_pattern = "*.json"
    
    # Exclure le fichier de référentiel des stations et metadata
    excluded_files = ["Référentiel_stations.json", "metadata.json"]
    
    # Lister tous les fichiers JSON correspondant au motif
    json_files = []
    for file in glob.glob(os.path.join(input_folder, file_pattern)):
        filename = os.path.basename(file)
        if filename not in excluded_files:
            json_files.append(file)
    
    if verbose:
        print(f"Trouvé {len(json_files)} fichiers JSON à traiter")
    
    # Vérifier s'il y a des fichiers à traiter
    if not json_files:
        print("Aucun fichier JSON trouvé correspondant aux critères.")
        return None
    
    # Préparer les structures pour stocker les données
    all_data = []
    
    # Charger le référentiel des stations pour les noms
    stations_file = os.path.join(input_folder, "Référentiel_stations.json")
    stations_by_code = {}
    
    if os.path.exists(stations_file):
        try:
            with open(stations_file, 'r', encoding='utf-8') as f:
                stations = json.load(f)
                for station in stations:
                    stations_by_code[station['codeUIC']] = station['shortLabel']
        except Exception as e:
            if verbose:
                print(f"Erreur lors du chargement du référentiel des stations: {e}")
    
    # Filtrer les fichiers par date si nécessaire
    if start_date or end_date:
        filtered_files = []
        for file in json_files:
            # Extraire la date du nom de fichier
            try:
                # Format attendu: train_number_YYYY-MM-DD.json
                basename = os.path.basename(file)
                parts = basename.split('_')
                if len(parts) >= 2:
                    date_part = parts[-1].replace('.json', '')
                    file_date = datetime.datetime.strptime(date_part, "%Y-%m-%d")
                    
                    # Vérifier si la date est dans la plage
                    if start_date:
                        start_date_obj = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                        if file_date < start_date_obj:
                            continue
                    
                    if end_date:
                        end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
                        if file_date > end_date_obj:
                            continue
                    
                    filtered_files.append(file)
            except Exception as e:
                if verbose:
                    print(f"Erreur lors du filtrage par date pour {file}: {e}")
        
        json_files = filtered_files
        
        if verbose:
            print(f"Après filtrage par date: {len(json_files)} fichiers")
    
    # Traiter chaque fichier JSON
    for i, file_path in enumerate(json_files):
        if verbose and (i % 10 == 0 or i == len(json_files) - 1):
            print(f"Traitement du fichier {i+1}/{len(json_files)}: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                train_data = json.load(f)
            
            # Extraire les informations de base
            train_number = train_data.get('circulation', {}).get('numero', '')
            journey_date = train_data.get('circulation', {}).get('date', '')
            
            if include_all_fields:
                # Format détaillé: inclut chaque siège à chaque desserte
                for desserte in train_data.get('dessertes', []):
                    desserte_code_uic = desserte.get('codeUIC', '')
                    desserte_rang = desserte.get('rang', '')
                    station_name = stations_by_code.get(desserte_code_uic, desserte_code_uic)
                    
                    for rame in desserte.get('rames', []):
                        for voiture in rame.get('voitures', []):
                            coach_number = voiture.get('numero', '')
                            
                            for place in voiture.get('places', []):
                                seat_number = place.get('numero', '')
                                classe = place.get('classe', '')
                                niveau = place.get('niveau', '')
                                statut = place.get('occupation', {}).get('statut', '')
                                flux_montant = place.get('occupation', {}).get('fluxMontant', False)
                                flux_descendant = place.get('occupation', {}).get('fluxDescendant', False)
                                
                                # Ajouter toutes les données dans une ligne
                                all_data.append({
                                    'train_number': train_number,
                                    'journey_date': journey_date,
                                    'desserte_rang': desserte_rang,
                                    'desserte_code_uic': desserte_code_uic,
                                    'station_name': station_name,
                                    'coach_number': coach_number,
                                    'seat_number': seat_number,
                                    'classe': classe,
                                    'niveau': niveau,
                                    'statut': statut,
                                    'flux_montant': 1 if flux_montant else 0,
                                    'flux_descendant': 1 if flux_descendant else 0
                                })
            else:
                # Format résumé: agrège par jour et par gare
                for desserte in train_data.get('dessertes', []):
                    desserte_code_uic = desserte.get('codeUIC', '')
                    desserte_rang = desserte.get('rang', '')
                    station_name = stations_by_code.get(desserte_code_uic, desserte_code_uic)
                    
                    # Compteurs
                    total_seats = 0
                    occupied_seats = 0
                    montees = 0
                    descentes = 0
                    
                    # Traiter chaque siège
                    for rame in desserte.get('rames', []):
                        for voiture in rame.get('voitures', []):
                            for place in voiture.get('places', []):
                                total_seats += 1
                                
                                statut = place.get('occupation', {}).get('statut', '')
                                flux_montant = place.get('occupation', {}).get('fluxMontant', False)
                                flux_descendant = place.get('occupation', {}).get('fluxDescendant', False)
                                
                                if statut == 'OCCUPE':
                                    occupied_seats += 1
                                
                                if flux_montant:
                                    montees += 1
                                
                                if flux_descendant:
                                    descentes += 1
                    
                    # Calculer le taux d'occupation
                    occupation_rate = 0
                    if total_seats > 0:
                        occupation_rate = (occupied_seats / total_seats) * 100
                    
                    # Ajouter les données agrégées
                    all_data.append({
                        'train_number': train_number,
                        'journey_date': journey_date,
                        'desserte_rang': desserte_rang,
                        'desserte_code_uic': desserte_code_uic,
                        'station_name': station_name,
                        'total_seats': total_seats,
                        'occupied_seats': occupied_seats,
                        'occupation_rate': round(occupation_rate, 2),
                        'montees': montees,
                        'descentes': descentes,
                        'bilan_flux': montees - descentes
                    })
        
        except Exception as e:
            if verbose:
                print(f"Erreur lors du traitement du fichier {file_path}: {e}")
    
    if not all_data:
        print("Aucune donnée n'a été extraite des fichiers JSON.")
        return None
    
    # Convertir en DataFrame pour faciliter la manipulation
    df = pd.DataFrame(all_data)
    
    # Trier les données
    if include_all_fields:
        df = df.sort_values(by=['journey_date', 'desserte_rang', 'coach_number', 'seat_number'])
    else:
        df = df.sort_values(by=['journey_date', 'desserte_rang'])
    
    # Enregistrer en CSV
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    if verbose:
        print(f"Données consolidées enregistrées dans {output_file}")
        print(f"Nombre total de lignes: {len(df)}")
    
    return output_file

def analyze_occupation_trends(
    csv_file: str,
    output_folder: Optional[str] = None,
    train_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyse les tendances d'occupation à partir du fichier CSV consolidé.
    
    Args:
        csv_file: Chemin du fichier CSV à analyser
        output_folder: Dossier pour enregistrer les graphiques (optionnel)
        train_number: Filtrer sur un numéro de train spécifique (optionnel)
    
    Returns:
        Dict[str, Any]: Résultats de l'analyse
    """
    import matplotlib.pyplot as plt
    import numpy as np
    import calendar
    
    print(f"Analyse des tendances d'occupation dans {csv_file}")
    
    # Charger les données
    df = pd.read_csv(csv_file)
    
    # Filtrer par train si nécessaire
    if train_number:
        df = df[df['train_number'] == train_number]
    
    # Convertir la date en objet datetime
    df['journey_date'] = pd.to_datetime(df['journey_date'])
    
    # Ajouter des colonnes pour l'analyse
    df['day_of_week'] = df['journey_date'].dt.day_name()
    df['month'] = df['journey_date'].dt.month_name()
    df['week'] = df['journey_date'].dt.isocalendar().week
    
    # Créer le dossier de sortie si nécessaire
    if output_folder:
        os.makedirs(output_folder, exist_ok=True)
    
    # 1. Analyser l'occupation globale par jour
    daily_avg = df.groupby(['journey_date', 'train_number'])['occupation_rate'].mean().reset_index()
    
    plt.figure(figsize=(15, 6))
    for train in daily_avg['train_number'].unique():
        train_data = daily_avg[daily_avg['train_number'] == train]
        plt.plot(train_data['journey_date'], train_data['occupation_rate'], '-', label=f'Train {train}')
    
    plt.title('Évolution du taux d\'occupation par jour')
    plt.xlabel('Date')
    plt.ylabel('Taux d\'occupation moyen (%)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    if output_folder:
        plt.savefig(os.path.join(output_folder, 'daily_occupation.png'))
    plt.show()
    
    # 2. Analyser l'occupation par jour de la semaine
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_avg = df.groupby(['day_of_week', 'train_number'])['occupation_rate'].mean().reset_index()
    
    plt.figure(figsize=(12, 6))
    for i, train in enumerate(weekly_avg['train_number'].unique()):
        train_data = weekly_avg[weekly_avg['train_number'] == train]
        # Créer un dataframe temporaire pour s'assurer que tous les jours sont présents
        temp_df = pd.DataFrame({'day_of_week': day_order})
        temp_df = temp_df.merge(train_data, on='day_of_week', how='left')
        temp_df = temp_df.sort_values(by='day_of_week', key=lambda x: pd.Categorical(x, categories=day_order, ordered=True))
        
        bar_width = 0.8 / len(weekly_avg['train_number'].unique())
        offset = (i - len(weekly_avg['train_number'].unique()) / 2 + 0.5) * bar_width
        
        plt.bar([x + offset for x in range(len(day_order))], temp_df['occupation_rate'],
                width=bar_width, label=f'Train {train}')
    
    plt.xticks(range(len(day_order)), day_order)
    plt.title('Taux d\'occupation moyen par jour de la semaine')
    plt.xlabel('Jour de la semaine')
    plt.ylabel('Taux d\'occupation moyen (%)')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    if output_folder:
        plt.savefig(os.path.join(output_folder, 'weekly_occupation.png'))
    plt.show()
    
    # 3. Analyser l'occupation par mois
    month_order = [calendar.month_name[i] for i in range(1, 13)]
    monthly_avg = df.groupby(['month', 'train_number'])['occupation_rate'].mean().reset_index()
    
    plt.figure(figsize=(15, 6))
    for i, train in enumerate(monthly_avg['train_number'].unique()):
        train_data = monthly_avg[monthly_avg['train_number'] == train]
        # Créer un dataframe temporaire pour s'assurer que tous les mois sont présents
        temp_df = pd.DataFrame({'month': [m for m in month_order if m != '']})
        temp_df = temp_df.merge(train_data, on='month', how='left')
        temp_df = temp_df.sort_values(by='month', key=lambda x: pd.Categorical(x, categories=month_order, ordered=True))
        
        bar_width = 0.8 / len(monthly_avg['train_number'].unique())
        offset = (i - len(monthly_avg['train_number'].unique()) / 2 + 0.5) * bar_width
        
        plt.bar([x + offset for x in range(len(month_order) - 1)], temp_df['occupation_rate'],
                width=bar_width, label=f'Train {train}')
    
    plt.xticks(range(len(month_order) - 1), [m for m in month_order if m != ''])
    plt.title('Taux d\'occupation moyen par mois')
    plt.xlabel('Mois')
    plt.ylabel('Taux d\'occupation moyen (%)')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    
    if output_folder:
        plt.savefig(os.path.join(output_folder, 'monthly_occupation.png'))
    plt.show()
    
    # 4. Analyser les montées et descentes
    station_flux = df.groupby(['station_name', 'train_number'])[['montees', 'descentes']].sum().reset_index()
    station_flux['net_flux'] = station_flux['montees'] - station_flux['descentes']
    
    plt.figure(figsize=(16, 8))
    for train in station_flux['train_number'].unique():
        train_data = station_flux[station_flux['train_number'] == train]
        # Trier par rang de desserte pour mieux visualiser le parcours
        train_data = train_data.sort_values(by='station_name')
        
        plt.figure(figsize=(16, 6))
        x = range(len(train_data))
        plt.bar(x, train_data['montees'], label='Montées', color='green')
        plt.bar(x, -train_data['descentes'], label='Descentes', color='red')
        plt.axhline(y=0, color='grey', linestyle='-', alpha=0.3)
        
        plt.title(f'Flux de passagers par gare - Train {train}')
        plt.xticks(x, train_data['station_name'], rotation=45, ha='right')
        plt.ylabel('Nombre de passagers')
        plt.legend()
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        if output_folder:
            plt.savefig(os.path.join(output_folder, f'passenger_flow_train_{train}.png'))
        plt.show()
    
    # 5. Heatmap de l'occupation par jour et par gare
    # Sélectionner un train pour la démonstration
    if train_number:
        selected_train = train_number
    else:
        selected_train = df['train_number'].iloc[0]
    
    train_df = df[df['train_number'] == selected_train]
    
    # Créer un pivot pour la heatmap (jours en Y, gares en X)
    pivot_df = train_df.pivot_table(
        values='occupation_rate',
        index='journey_date',
        columns='station_name',
        aggfunc='mean'
    )
    
    # Échantillonner pour réduire la taille (si nécessaire)
    if len(pivot_df) > 50:
        pivot_df = pivot_df.resample('7D').mean()
    
    plt.figure(figsize=(16, 10))
    plt.imshow(pivot_df, cmap='Blues', aspect='auto')
    plt.colorbar(label='Taux d\'occupation (%)')
    plt.title(f'Heatmap du taux d\'occupation par jour et par gare - Train {selected_train}')
    
    # Configurer les étiquettes des axes
    plt.yticks(range(len(pivot_df)), pivot_df.index.strftime('%Y-%m-%d'), fontsize=8)
    plt.xticks(range(len(pivot_df.columns)), pivot_df.columns, rotation=45, ha='right', fontsize=8)
    
    plt.tight_layout()
    
    if output_folder:
        plt.savefig(os.path.join(output_folder, f'occupation_heatmap_train_{selected_train}.png'))
    plt.show()
    
    # Retourner quelques statistiques
    stats = {
        'num_trains': len(df['train_number'].unique()),
        'num_days': len(df['journey_date'].unique()),
        'num_stations': len(df['station_name'].unique()),
        'avg_occupation': df['occupation_rate'].mean(),
        'max_occupation': df['occupation_rate'].max(),
        'min_occupation': df['occupation_rate'].min(),
        'total_montees': df['montees'].sum(),
        'total_descentes': df['descentes'].sum(),
        'trains': df['train_number'].unique().tolist()
    }
    
    return stats

# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple: convertir tous les fichiers d'un dossier en CSV
    input_folder = "./train_data"
    output_file = "./train_data_consolidated.csv"
    
    consolidated_file = consolidate_train_data_to_csv(
        input_folder=input_folder,
        output_file=output_file,
        include_all_fields=False,  # Format résumé par jour/gare
        verbose=True
    )
    
    if consolidated_file:
        # Analyser les tendances
        stats = analyze_occupation_trends(
            csv_file=consolidated_file,
            output_folder="./train_data_analysis",
            train_number=None  # Analyser tous les trains
        )
        
        print("\nStatistiques d'occupation:")
        for key, value in stats.items():
            if key != 'trains':
                print(f"  - {key}: {value}")
        print(f"  - Trains: {', '.join(stats['trains'])}")