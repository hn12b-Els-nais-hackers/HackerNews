from django.urls import path
from .api_views import (
    UserProfileAPI,
    SubmissionAPI,
    SubmissionDetailAPI,
    CommentAPI,
    CommentDetailAPI,
    UserContentAPI,
    SubmissionSearchAPI,
    SubmissionCommentsAPI,
)

urlpatterns = [
    # User Profile
    path('profile/<str:username>/', UserProfileAPI.as_view(), name='api-profile-detail'),
    
    # User-specific content - simplified to one endpoint with query parameter
    path('user/<str:username>/content/', UserContentAPI.as_view(), name='api-user-content'),
    
    # Submissions
    path('submissions/', SubmissionAPI.as_view(), name='api-submissions'),
    path('submissions/<int:submission_id>/', SubmissionDetailAPI.as_view(), name='api-submission-detail'),
    path('submissions/search/', SubmissionSearchAPI.as_view(), name='api-submission-search'),

    # Comments
    path('submissions/<int:submission_id>/comments/', SubmissionCommentsAPI.as_view(), name='api-submission-comments'),
    path('comments/', CommentAPI.as_view(), name='api-comments'),
    path('comments/<int:comment_id>/', CommentDetailAPI.as_view(), name='api-comment-detail'),
]
