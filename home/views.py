from django.shortcuts import render
from django.http import HttpResponse
from .models import Profile
from .github_api import get_github_user
from .cv_generator import build_cv_pdf

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


def download_cv(request):
    """Generate a fresh, ATS-friendly CV PDF from live GitHub + portfolio data.

    Built on every request (not stored on disk), so it always reflects the
    latest GitHub repos, education entries, and admin-edited CV content with
    no manual regeneration step.
    """
    profile = Profile.objects.first()
    cv_url = request.build_absolute_uri()
    buf, filename = build_cv_pdf(profile, cv_url=cv_url)
    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response