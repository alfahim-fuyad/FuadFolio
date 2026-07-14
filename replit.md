# fuadFolio

A personal portfolio website for Md. Al Fahim Fuyad, built with Django.

## Stack

- **Language**: Python 3.12
- **Framework**: Django 6.0 (upgraded from 4.2 during setup — the pinned 4.2 wheel is blocked by Replit's package firewall, so `requirements.txt` was regenerated via `pip freeze` against the latest installable versions)
- **Database**: PostgreSQL (Replit-managed, via `DATABASE_URL`). Falls back to SQLite if `DATABASE_URL` is not set.
- **Static files**: WhiteNoise
- **Production server**: Gunicorn

## Project Layout

- `FuadFolio/` — Django project (settings, urls, wsgi)
- `home/`, `about/`, `portfolio/`, `contact/` — Django apps
- `templates/` — shared HTML templates
- `static/` — source static assets (css, images)
- `staticfiles/` — collected static files (used in production)
- `manage.py` — Django management entrypoint

## Running

The `Start application` workflow runs:

```
python manage.py runserver 0.0.0.0:5000
```

The app listens on port 5000 and is served through the Replit preview proxy.

## Configuration Notes

- `ALLOWED_HOSTS = ['*']` and `CSRF_TRUSTED_ORIGINS` cover the Replit preview proxy.
- The repo originally pointed at an external MySQL database (Clever Cloud, via `.env`); the app now uses the Replit-managed PostgreSQL database via `DATABASE_URL` and falls back to SQLite if that's unset. Migrations have been applied to the Postgres database.
- `DEBUG` defaults to `True` in development; set the `DEBUG` env var to `False` for production behavior.
- WhiteNoise is enabled for serving static files.

## Site identity & GitHub-driven projects

- `FuadFolio/settings.py` defines `SITE_GITHUB_USERNAME`, `SITE_EMAIL`, `SITE_LINKEDIN_URL`, `SITE_FACEBOOK_URL` — the single source of truth for contact/social info, overridable via env vars.
- `home/context_processors.py` exposes these as `{{ site.* }}` in every template (nav, footer, hero, about, contact) instead of hardcoding the email/GitHub link in six places. It also exposes `site.cv_url` (the uploaded `Profile.resume`, if any) so the navbar "Download CV" button always points at the latest uploaded file.
- The navbar "Hire Me" button was replaced with "Download CV" — it links to `site.cv_url` when a CV is uploaded in `/admin/` (`Profile.resume`), otherwise falls back to the `home:download_cv` view, which 404s with a clear message until a CV is uploaded.
- `home/github_api.py` calls the public GitHub REST API (no token needed since repos are public) and caches responses for 30 minutes.
  - `portfolio/views.py` now renders live public repos from `https://github.com/<SITE_GITHUB_USERNAME>` — pushing a new public repo makes it appear on `/portfolio/` automatically, no admin edit needed. Forked repos are excluded.
  - `home/views.py` uses the profile's uploaded photo (`home.Profile`, editable in `/admin/`) if set, otherwise falls back to the real GitHub avatar for the same reason `static/images/fuad.png` was an empty placeholder file.
- The old `portfolio.Project` model/admin still exists but is no longer used by the projects page (kept for reference, not wired into any view).

## Deployment

Configured for Replit Autoscale:

- Build: `python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Run: `gunicorn --bind=0.0.0.0:5000 --reuse-port FuadFolio.wsgi:application`
