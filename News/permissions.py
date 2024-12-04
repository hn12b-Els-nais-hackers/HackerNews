from rest_framework.permissions import BasePermission
from django.contrib.auth.models import User
from News.models import UserProfile

class IsAPIKeyValid(BasePermission):
    """
    Custom permission to check if the API key is valid and corresponds to the authenticated user.
    """

    def has_permission(self, request, view):
        api_key = request.headers.get('API-Key')
        if not api_key:
            return False

        # Find the user associated with this API key
        try:
            user_profile = UserProfile.objects.get(api_key=api_key)
            request.user = user_profile.user  # Attach user to the request object
            return True
        except UserProfile.DoesNotExist:
            return False
