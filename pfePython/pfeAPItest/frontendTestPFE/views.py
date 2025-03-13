from django.shortcuts import render

def index(request):
    # Pour le débogage, ajoutez un contexte simple
    context = {'debug_message': 'La vue fonctionne correctement'}
    return render(request, 'frontendTestPFE/index.html', context)