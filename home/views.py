from django.shortcuts import render
from .models import Profile
from .github_api import get_github_user

def home(request):
    profile = Profile.objects.first()

    # Prefer a photo uploaded in the admin. Otherwise fall back to the real
    # GitHub avatar for the configured profile, so the hero always shows an
    # actual picture instead of a broken/placeholder image.
    avatar_url = None
    if profile and profile.photo:
        avatar_url = profile.photo.url
    else:
        github_user = get_github_user()
        if github_user:
            avatar_url = github_user.get('avatar_url')

    return render(request, 'home/home.html', {'profile': profile, 'avatar_url': avatar_url})