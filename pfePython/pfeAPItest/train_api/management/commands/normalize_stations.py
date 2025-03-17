# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import os
from django.conf import settings
from train_api.utils.json_utils import normalize_json_file

class Command(BaseCommand):
    help = 'Normalise le fichier référentiel des gares au format tableau JSON standard'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Chemin vers le fichier à normaliser (par défaut: data/Référentiel_stations.json)',
        )
    
    def handle(self, *args, **options):
        """
        Exécute la commande pour normaliser le fichier de référentiel des gares
        """
        data_folder = os.path.join(settings.BASE_DIR, 'data/')
        
        if options['file']:
            # Utiliser le chemin spécifié
            file_path = options['file']
            if not os.path.isabs(file_path):
                # Si le chemin n'est pas absolu, le considérer comme relatif au dossier data
                file_path = os.path.join(data_folder, file_path)
        else:
            # Utiliser le chemin par défaut
            file_path = os.path.join(data_folder, 'Référentiel_stations.json')
        
        if not os.path.exists(file_path):
            raise CommandError(f"Le fichier {file_path} n'existe pas.")
        
        self.stdout.write(self.style.WARNING(f"Normalisation du fichier {file_path}..."))
        
        if normalize_json_file(file_path):
            self.stdout.write(self.style.SUCCESS(f"Le fichier {file_path} a été normalisé avec succès."))
        else:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la normalisation du fichier {file_path}."))