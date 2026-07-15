---
name: Stale nested duplicate Django project copy
description: A full duplicate Django project can end up committed as a subfolder sharing the same name as the real settings package — deleting it naively can delete the real package too.
---

This repo had a workspace-root `FuadFolio/` directory that was supposed to be just the Django
settings package (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`, `__init__.py`) — but it also
contained an entire stale second copy of the whole project (its own `manage.py`, app dirs,
`static/`/`staticfiles/`, `db.sqlite3`, and a committed `.env` with real-looking DB
credentials/SECRET_KEY), apparently left over from an earlier `django-admin startproject` run
before the project was flattened into the repo root.

**Why this matters:** a hosting platform (Render) had its "Root Directory" pointed at that stale
subfolder, so it deployed the old code/CSS instead of the current one — symptom was "CSS doesn't
work" in production while the dev preview looked fine. Also, `git rm -r --cached FuadFolio/`
(or `rm -rf FuadFolio/`) to clean up the duplicate will also delete the real settings package,
since both live under the same path prefix — this broke the running app until the 5 real files
were restored from a `mv`'d backup.

**How to apply:** before deleting a directory that looks like a stale duplicate, `diff` its
files against the ones actually referenced by `manage.py`/`WSGI_APPLICATION`/`DJANGO_SETTINGS_MODULE`,
and copy out anything still in active use *before* removing the directory tree. Also check
hosting-platform "Root Directory" settings when a deployed site serves visibly older
content/styling than the repo's current HEAD. Never commit `.env`/`db.sqlite3`; if one was ever
committed to a public repo, treat any real credentials in it as compromised and rotate them,
since removing the file from tracking does not purge it from git history.
