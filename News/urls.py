from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubmissionViewSet,
    CommentViewSet,
    UserProfileViewSet,
    CurrentUserView,
    FavoriteSubmissionsListView,
    HiddenSubmissionsListView,
)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Your API",
        default_version='v1',
        description="API for your application",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@yourapp.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'submissions', SubmissionViewSet, basename='submission')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'user-profiles', UserProfileViewSet, basename='userprofile')

urlpatterns = [
    path('api/', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("api/current-user/", CurrentUserView.as_view(), name="current-user"),
    path("api/favorites/", FavoriteSubmissionsListView.as_view(), name="favorite-submissions"),
    path("api/hidden/", HiddenSubmissionsListView.as_view(), name="hidden-submissions"),
]
