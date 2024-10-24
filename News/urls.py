from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.news, name='news'),             
    path('newest/', views.newest, name='newest'),   
    path('submit/', views.submit, name='submit'), 
    path('ask/', views.ask, name='ask'),
    path('comments/', views.comments, name='comments'), 
    path('login/', views.login, name='login'),   
    path('threads/', views.threads, name='threads'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('add_comment/', views.add_comment, name='add_comment'),
    # Página de perfil del usuario
    path('profile/<str:username>/', views.profile_view, name='profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  

