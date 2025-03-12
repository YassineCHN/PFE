from django.core.management.base import BaseCommand
from train_api.models import Station
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Charge les données de stations depuis le fichier Référentiel_stations.json'

    def handle(self, *args, **options):
        data_folder = os.path.join(settings.BASE_DIR, 'data/')
        stations_file = f"{data_folder}Référentiel_stations.json"
        
        try:
            with open(stations_file, 'r', encoding='utf-8') as file:
                stations_data = json.load(file)
                
                # Supprime les anciennes données si nécessaire
                Station.objects.all().delete()
                
                # Charge les nouvelles données
                for station in stations_data:
                    Station.objects.create(
                        code_uic=station['codeUIC'],
                        label=station['label'],
                        short_label=station['shortLabel'],
                        long_label=station['longLabel']
                    )
                
                self.stdout.write(self.style.SUCCESS(f'Successfully loaded {len(stations_data)} stations'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading stations: {e}'))# -*- coding: utf-8 -*-

