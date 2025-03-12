from django.shortcuts import render, redirect
from django.http import HttpResponse
from .api import get_seat_occupation

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