# FuadFolio

A personal portfolio website built with Django 4.2.

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

## Deployment

Configured for Replit Autoscale:

- Build: `python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Run: `gunicorn --bind=0.0.0.0:5000 --reuse-port FuadFolio.wsgi:application`
