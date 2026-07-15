---
name: Neon/Render/Railway Postgres SSL gotcha
description: DATABASE_URL ssl_require must not be hardcoded True if the same settings.py also runs against Replit's own dev Postgres.
---

Neon (and most managed Postgres used on Render/Railway) requires SSL, but Replit's own
built-in dev Postgres does NOT support SSL on its internal network. If a Django project
targets both (dev on Replit, prod on Render/Railway with Neon) via the same
`dj_database_url.config(ssl_require=...)` call, hardcoding `ssl_require=True` breaks the
Replit dev workflow with `server does not support SSL, but SSL was required`.

**Why:** one settings.py serves multiple deploy targets with different Postgres providers
that have opposite SSL support.

**How to apply:** derive `ssl_require` from the environment instead of hardcoding it, e.g.
`ssl_require=not DEBUG` (dev/Replit typically runs DEBUG=True with no-SSL Postgres; prod
platforms are deployed with DEBUG=False and a Neon/managed URL that supports SSL).
