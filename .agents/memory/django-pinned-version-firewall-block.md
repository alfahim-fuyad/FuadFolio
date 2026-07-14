---
name: Django pinned-version firewall block
description: Old pinned Django wheel versions (e.g. 4.2) can be rejected by Replit's package firewall (403), even though the package itself is fine.
---

When installing Python packages via `installLanguagePackages`, a pinned old version like `Django==4.2` can fail with a 403 from `package-firewall.replit.local` while the exact same package installs fine unpinned (resolves to latest, e.g. Django 6.0.7).

**Why:** The package firewall appears to block specific old wheel URLs/versions rather than the package overall. Retrying with an unpinned install (or the latest version) is the standard firewall-recovery path from the package-management skill.

**How to apply:** If a pinned dependency install returns a 403 from the package firewall, retry installing that package unpinned (latest). Then regenerate the lockfile/requirements (`pip freeze`) to match what's actually installed, and re-check the app for breaking API changes introduced by the version jump (propose a follow-up task to verify rather than assuming compatibility).
