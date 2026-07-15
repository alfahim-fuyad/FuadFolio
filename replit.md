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
- `home/context_processors.py` exposes these as `{{ site.* }}` in every template (nav, footer, hero, about, contact) instead of hardcoding the email/GitHub link in six places.
- The navbar "Hire Me" button was replaced with "Download CV" (`home:download_cv`). It does NOT serve a static uploaded file — `home/cv_generator.py` builds an ATS-friendly PDF (ReportLab) on every request from live data: GitHub repos (via `github_api.py`), `about.Education` rows, and `Profile` fields (full_name/title/location/summary/skills/experience/certifications, editable in `/admin/`). Editing any of those sources changes the very next download — no regeneration step, nothing cached to disk.
- `home/github_api.py` calls the public GitHub REST API (no token needed since repos are public) and caches responses for 30 minutes.
  - `portfolio/views.py` now renders live public repos from `https://github.com/<SITE_GITHUB_USERNAME>` — pushing a new public repo makes it appear on `/portfolio/` automatically, no admin edit needed. Forked repos are excluded.
  - `home/views.py` uses the profile's uploaded photo (`home.Profile`, editable in `/admin/`) if set, otherwise falls back to the real GitHub avatar for the same reason `static/images/fuad.png` was an empty placeholder file.
- The old `portfolio.Project` model/admin still exists but is no longer used by the projects page (kept for reference, not wired into any view).

## Deployment

Configured for Replit Autoscale:

- Build: `python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Run: `gunicorn --bind=0.0.0.0:5000 --reuse-port FuadFolio.wsgi:application`

### Deploying to Render / Koyeb with Neon Postgres

`render.yaml` and `koyeb.yaml` are both in the repo. Same required env vars on
either platform (set them in the platform's dashboard, not committed to git):

| Key | Value |
|---|---|
| `SECRET_KEY` | a long random string (Render generates one automatically; Koyeb needs one set manually) |
| `DEBUG` | `False` |
| `DATABASE_URL` | your Neon connection string, e.g. `postgresql://user:pass@host/db?sslmode=require` |
| `SITE_GITHUB_USERNAME` | `alfahim-fuyad` |
| `SITE_EMAIL` | `md.alfahim.fuyad@gmail.com` |
| `SITE_LINKEDIN_URL` | `https://www.linkedin.com/in/al-fahim-36126636b` |
| `SITE_FACEBOOK_URL` | `https://www.facebook.com/alfahim07` |
| `CSRF_EXTRA_ORIGINS` | only needed if you attach a custom domain, e.g. `https://yourdomain.com` |

`FuadFolio/settings.py` already trusts `*.onrender.com`, `*.koyeb.app`,
`*.up.railway.app`/`*.railway.app` for CSRF. After the first deploy, run
`python manage.py createsuperuser` as a one-off shell command on that platform
to get into `/admin/` and fill in `Profile` and `Education`.
