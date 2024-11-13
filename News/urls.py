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
    path('submission/<int:submission_id>/edit/', views.edit_submission, name='edit_submission'),
    path('submission/<int:submission_id>/delete/', views.delete_submission, name='delete_submission'),
    path('search/', views.search, name='search'),

    # Página de perfil del usuario
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('profile/<str:username>/submissions/', views.user_submissions, name='user_submissions'),
    path('user/<str:username>/comments/', views.user_comments, name='user_comments'),
    path('user/<str:username>/upvoted/', views.user_upvoted, name='user_upvoted'),
    path('upvote/<int:submission_id>/', views.upvote_submission, name='upvote_submission'),
    path('unvote/<int:submission_id>/', views.unvote_submission, name='unvote_submission'),
    path('hide/<int:submission_id>/', views.hide_submission, name='hide_submission'),
    path('hidden/', views.hidden_submissions, name='hidden_submissions'),
    path('unhide/<int:submission_id>/', views.unhide_submission, name='unhide_submission'),
    path('comment/<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('fav/<int:submission_id>/', views.fav_submission, name='fav_submission'),
    path('favorites/', views.favorite_submissions, name='favorite_submissions'),
    path('vote/comment/<int:comment_id>/', views.vote_comment, name='vote_comment'),
    path('fav/comment/<int:comment_id>/', views.fav_comment, name='fav_comment'),
    path('hide/comment/<int:comment_id>/', views.hide_comment, name='hide_comment'),
    path('unhide/comment/<int:comment_id>/', views.unhide_comment, name='unhide_comment'),
    path('test-upload/', views.test_s3_upload, name='test_s3_upload'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  

