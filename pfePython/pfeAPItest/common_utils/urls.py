from django.urls import path
from . import views

app_name = 'common_utils'

urlpatterns = [
    path('', views.home, name='home'),

]