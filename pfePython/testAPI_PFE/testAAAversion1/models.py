from django.db import models

# Create your models here.


class Station(models.Model):
    """
    Modèle pour stocker les informations des gares
    """
    code_uic = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=100)
    short_label = models.CharField(max_length=50)
    long_label = models.CharField(max_length=150)

    def __str__(self):
        return self.short_label