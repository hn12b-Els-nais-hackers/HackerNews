from django.urls import path
from .api_views import UserProfileAPI, SubmissionAPI, CommentAPI

urlpatterns = [
    path('user/<str:username>/', UserProfileAPI.as_view(), name='api-user-profile'),
    path('user/<str:username>/submissions/', SubmissionAPI.as_view(), name='api-user-submissions'),
    path('user/<str:username>/comments/', CommentAPI.as_view(), name='api-user-comments'),
    # Other API routes...
]
