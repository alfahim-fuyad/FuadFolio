# fuadFolio

Personal portfolio website for **Md. Al Fahim Fuyad** — Data Scientist, ML Engineer, and AI Builder. Built with Django and a hand-crafted, fully responsive design system.

Live sections: Home (hero, skills, services), About (bio + education journey), Projects (live GitHub repos), and Contact.

## Stack

- **Language**: Python 3.12
- **Framework**: Django 6.0
- **Database**: PostgreSQL (Replit-managed, via `DATABASE_URL`). Falls back to SQLite if `DATABASE_URL` is not set.
- **Static files**: WhiteNoise
- **Production server**: Gunicorn

## Project Layout

- `FuadFolio/` — Django project package (settings, urls, wsgi/asgi)
- `home/`, `about/`, `portfolio/`, `contact/` — Django apps
- `templates/` — shared HTML templates
- `static/` — source static assets (css, images, favicon)
- `staticfiles/` — collected static files (used in production)
- `media/` — user-uploaded files (profile photo, CV/resume, education images)
- `manage.py` — Django management entrypoint

## Running

The `Start application` workflow runs:

```
python manage.py runserver 0.0.0.0:5000
```

The app listens on port 5000 and is served through the Replit preview proxy.

## Features

- **Responsive design system** — one CSS file with breakpoints tuned for desktop, laptop, tablet, and mobile; consistent spacing/alignment across all of them.
- **GitHub-driven Projects page** — `home/github_api.py` pulls live public repos from `https://api.github.com/users/<SITE_GITHUB_USERNAME>/repos` (cached 30 minutes); push a new public repo and it appears automatically, no admin edit needed.
- **Centralized site identity** — `FuadFolio/settings.py` defines `SITE_GITHUB_USERNAME`, `SITE_EMAIL`, `SITE_LINKEDIN_URL`, `SITE_FACEBOOK_URL`; exposed to every template via `home/context_processors.py` as `{{ site.* }}` instead of hardcoding contact info in multiple places.
- **Download CV (auto-generated, ATS-friendly)** — the navbar "Download CV" button (route: `home/cv/`, view: `home.views.download_cv`) builds a clean, modern PDF resume on every request using `home/cv_generator.py` (ReportLab). It pulls:
  - **Projects** live from the GitHub REST API (top repos by stars/recency) — a new public repo shows up automatically.
  - **Education** live from the `about.Education` admin model.
  - **Name, title, summary, skills, experience, certifications** from the `Profile` row in `/admin/` — edit any of these and the very next download reflects it. Nothing is cached to disk, so there's no separate "regenerate" step.
- **Profile photo fallback** — uses the uploaded `Profile.photo` if set in `/admin/`, otherwise falls back to the real GitHub avatar.
- **Education Journey** — About page lists School (Anjuman Adarsha Govt. High School, Netrakona), College (Agricultural University College), and University (East West University) with real logos/photos, editable via `/admin/` (`about.Education`).

## Configuration Notes

- `ALLOWED_HOSTS = ['*']` and `CSRF_TRUSTED_ORIGINS` cover the Replit preview proxy.
- `DEBUG` defaults to `True` in development; set the `DEBUG` env var to `False` for production behavior.
- WhiteNoise serves static files; media (photo, CV, education images) is served via Django in development and should be backed by persistent/object storage in production.
- All contact/social URLs (`SITE_EMAIL`, `SITE_LINKEDIN_URL`, `SITE_FACEBOOK_URL`, `SITE_GITHUB_USERNAME`) are overridable via environment variables without touching template code.

## Admin

Manage content at `/admin/`:
- **Profile** — profile photo plus CV content fields (title, location, summary, skills, experience, certifications) that feed the auto-generated "Download CV" PDF.
- **Education** — School/College/University entries shown on the About page and included in the generated CV.

## Deployment

Configured for Replit Autoscale:

- Build: `python manage.py collectstatic --noinput && python manage.py migrate --noinput`
- Run: `gunicorn --bind=0.0.0.0:5000 --reuse-port FuadFolio.wsgi:application`
