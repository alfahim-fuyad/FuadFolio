"""Small helper for pulling public data from the GitHub REST API.

Everything here is read-only and only touches public endpoints, so no
GitHub token is required as long as the profile's repositories are public.
Responses are cached briefly so page loads don't hammer GitHub's API and
so we stay comfortably under its unauthenticated rate limit.
"""
import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
REQUEST_TIMEOUT = 6  # seconds
CACHE_TIMEOUT = 60 * 30  # 30 minutes


def get_github_user(username=None):
    """Fetch the public GitHub profile (name, avatar, bio, etc.)."""
    username = username or settings.SITE_GITHUB_USERNAME
    cache_key = f"github_user:{username}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(f"{API_BASE}/users/{username}", timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("GitHub profile fetch failed for %s: %s", username, exc)
        data = None

    cache.set(cache_key, data, CACHE_TIMEOUT)
    return data


def get_github_repos(username=None):
    """Fetch public repositories, newest-pushed first, forks excluded."""
    username = username or settings.SITE_GITHUB_USERNAME
    cache_key = f"github_repos:{username}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    repos = []
    try:
        resp = requests.get(
            f"{API_BASE}/users/{username}/repos",
            params={"per_page": 100, "sort": "pushed", "direction": "desc"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json()
        for repo in raw:
            if repo.get("fork"):
                continue
            repos.append({
                "name": repo.get("name"),
                "description": repo.get("description"),
                "url": repo.get("html_url"),
                "homepage": repo.get("homepage") or None,
                "language": repo.get("language"),
                "topics": repo.get("topics") or [],
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "updated_at": repo.get("pushed_at"),
            })
    except requests.RequestException as exc:
        logger.warning("GitHub repos fetch failed for %s: %s", username, exc)
        repos = None  # signal "couldn't reach GitHub" vs "no public repos"

    cache.set(cache_key, repos, CACHE_TIMEOUT)
    return repos
