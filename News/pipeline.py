from .models import UserProfile

def create_user_profile(backend, user, response, *args, **kwargs):
    if not UserProfile.objects.filter(user=user).exists():
        UserProfile.objects.create(user=user)