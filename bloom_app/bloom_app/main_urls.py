# bloom_app/main_urls.py

from django.urls import path
from django.shortcuts import render

def home(request):
    return render(request, 'main.html')

urlpatterns = [
    path('', home, name='home'),
]