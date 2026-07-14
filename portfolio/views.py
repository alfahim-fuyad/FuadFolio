from django.shortcuts import render
from home.github_api import get_github_repos

def portfolio(request):
    repos = get_github_repos()
    github_error = repos is None
    return render(request, 'portfolio/portfolio.html', {
        'repos': repos or [],
        'github_error': github_error,
    })
