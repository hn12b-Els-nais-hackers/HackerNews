from django.http import JsonResponse
from News.models import UserProfile

class APIKeyAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):  # Restrict to API routes
            api_key = request.headers.get('Authorization')
            if not api_key:
                return JsonResponse({'error': 'API key missing'}, status=401)
            try:
                user_profile = UserProfile.objects.get(api_key=api_key)
                request.user = user_profile.user  # Attach user to request
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'Invalid API key'}, status=403)
        return self.get_response(request)
