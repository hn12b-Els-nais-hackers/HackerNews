
from django.urls import path
from . import views

urlpatterns = [
    path('', views.news, name='news'),             
    path('newest/', views.newest, name='newest'),   
    path('submit/', views.submit, name='submit'), 
    path('about/', views.about, name='about'),  
]
