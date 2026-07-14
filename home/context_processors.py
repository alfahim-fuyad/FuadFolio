from django.conf import settings
from .models import Profile


def site_info(request):
    """Expose site-wide contact/social info to every template as `site`."""
    username = settings.SITE_GITHUB_USERNAME

    cv_url = None
    profile = Profile.objects.first()
    if profile and profile.resume:
        cv_url = profile.resume.url

    return {
        'site': {
            'email': settings.SITE_EMAIL,
            'github_username': username,
            'github_url': f'https://github.com/{username}',
            'linkedin_url': settings.SITE_LINKEDIN_URL,
            'facebook_url': settings.SITE_FACEBOOK_URL,
            'cv_url': cv_url,
        }
    }
