
from django.urls import path
from . import views

urlpatterns = [
    path('', views.news, name='news'),             
    path('newest/', views.newest, name='newest'),   
    path('submit/', views.submit, name='submit'), 
    path('ask/', views.ask, name='ask'),
    path('comments/', views.comments, name='comments'), 
    path('login/', views.login, name='login'),   
    path('threads/', views.threads, name='threads'), 
    path('submission/<int:submission_id>/', views.submission_detail, name='submission_detail'),
    path('submission/<int:submission_id>/edit/', views.edit_submission, name='edit_submission'),
]
