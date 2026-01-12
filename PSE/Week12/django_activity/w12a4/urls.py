"""
Week 12 - Activity 4: Initial Web- APP with Django
Develop a sample project as follows to kick-start learning Django.
Help sample:
from django.http import HttpResponse
def welcome(request, name):
    A simple Django view that takes a name from the URL
    and returns a personalized welcome message.
    return HttpResponse(f"<h1>Welcome {name} to Django!</h1>")

urls.py
Eduardo JR Ilagan
"""

from django.urls import path
from .django_w12_a4 import welcome

urlpatterns = [
    path('welcome/<str:name>/', welcome, name='welcome'),
]
