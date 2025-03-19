from django.shortcuts import render

# Create your views here.
def home(request):
    """
    Vue de la page d'accueil principale avec les vignettes de navigation
    """
    return render(request, 'common_utils/home.html')