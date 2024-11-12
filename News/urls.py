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
    path('submission/<int:submission_id>/comment/', views.create_comment, name='create_comment'),
    path('submission/<int:submission_id>/', views.submission_comments, name='submission_comments'),
    # Página de perfil del usuario
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('upvote/<int:submission_id>/', views.upvote_submission, name='upvote_submission'),
    path('unvote/<int:submission_id>/', views.unvote_submission, name='unvote_submission'),
    path('hide/<int:submission_id>/', views.hide_submission, name='hide_submission'),
    path('hidden/', views.hidden_submissions, name='hidden_submissions'),
    path('unhide/<int:submission_id>/', views.unhide_submission, name='unhide_submission'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  