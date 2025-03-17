from django.core.management.base import BaseCommand, CommandError
import os
import shutil
from django.conf import settings
from train_api.utils.json_utils import normalize_json_file

class Command(BaseCommand):
    help = 'Normalise un fichier référentiel des gares et remplace celui dans le dossier data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'source_file',
            type=str,
            help='Chemin vers le fichier source à normaliser et à copier',
        )
        parser.add_argument(
            '--destination',
            type=str,
            default='Référentiel_stations.json',
            help='Nom du fichier de destination dans le dossier data (par défaut: Référentiel_stations.json)',
        )
    
    def handle(self, *args, **options):
        """
        Exécute la commande pour normaliser le fichier source et remplacer le référentiel
        """
        source_file = options['source_file']
        destination_name = options['destination']
        data_folder = os.path.join(settings.BASE_DIR, 'data/')
        
        # S'assurer que le dossier data existe
        if not os.path.exists(data_folder):
            os.makedirs(data_folder)
        
        # Chemin de destination final
        destination_file = os.path.join(data_folder, destination_name)
        
        # Vérifier que le fichier source existe
        if not os.path.exists(source_file):
            raise CommandError(f"Le fichier source {source_file} n'existe pas.")
        
        self.stdout.write(self.style.WARNING(f"Normalisation du fichier {source_file}..."))
        
        # Normaliser le fichier source
        if normalize_json_file(source_file):
            self.stdout.write(self.style.SUCCESS(f"Le fichier {source_file} a été normalisé avec succès."))
            
            # Copier le fichier normalisé vers la destination
            try:
                shutil.copy2(source_file, destination_file)
                self.stdout.write(self.style.SUCCESS(
                    f"Le fichier normalisé a été copié avec succès vers {destination_file}."
                ))
            except Exception as e:
                raise CommandError(f"Erreur lors de la copie du fichier: {e}")
        else:
            raise CommandError(f"Erreur lors de la normalisation du fichier {source_file}.")