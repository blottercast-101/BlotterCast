# BlotterCast — Python (Flask) Edition

The full Python rebuild of BlotterCast's backend: **Flask + SQLAlchemy**,
replacing PHP/MySQL entirely, ready to deploy with PostgreSQL.

**Status: Complete.** Every module from the original PHP backend has been
ported and tested:

| Module | What it covers |
|---|---|
| Auth | Login/logout, **email OTP multi-factor authentication (mandatory for all accounts)**, session timeout, account lockout, forced password change |
| Records | Incidents, Blotter, Settlements (full CRUD + RBAC) |
| Documents | Census, Barangay Clearance, Certificate of Residency / Non-Residency, Certificate of Indigency, blotter-record check |
| Analytics | Dashboard summary, heatmap, yearly trends, zones |
| Reports | PDF reports (ReportLab) — Incident Summary, Settlement Compliance, Trend Analysis, Predictive Risk — plus CSV/Excel export, with download & history log |
| Exports | The 3 official .xlsx forms (Settlement Monitoring, Blotter Record, Blotter Entry 2025), byte-for-byte matching the original column layout |
| Blotter Import | Upload `.xlsx`/`.csv` in the Blotter Record export format to bulk-create records |
| Users | Account management, signature upload, audit log |
| Settings | System settings, ML model selection, letterhead info, database backups |
| Notifications | High-priority incidents, overdue settlements, high-risk zone alerts |
| ML Proxy | Auto-starts and forwards to `ml/service.py`, same as the original |

Certificates (Clearance/Indigency/Residency/Non-Residency) print via the
browser's native print dialog over the letterhead images already bundled in
the frontend — that worked out of the box and needed no backend changes.

## Why it's structured this way

The frontend (`frontend/`) is untouched — same HTML/CSS/JS as before. It
calls `/api/auth.php?action=login`, `/api/records.php?type=incidents`, etc.
The Flask app defines routes at those *exact* paths, so the browser doesn't
know or care that PHP is gone.

## Project layout

```
app/
  config.py          # env-based config: DATABASE_URL, SECRET_KEY, cookie flags, SMTP/MFA settings
  extensions.py       # the SQLAlchemy() instance
  models.py           # every table from schema.sql, plus otp_codes
  permissions.py      # the role permission matrix + login/permission decorators
  helpers.py          # sequence numbers, age calc, resident name matching, date parsing
  email.py             # sends MFA OTP codes over SMTP (or logs them locally if unconfigured)
  blueprints/
    auth.py            # /api/auth.php  (login -> email OTP -> session)
    records.py         # /api/records.php      (incidents, blotter, settlements)
    documents.py        # /api/documents.php    (census, clearance, residency,
                        #   non_residency, indigency, blotter_check, or_peek)
    analytics.py        # /api/analytics.php    (dashboard, heatmap, trends, zones)
    reports.py           # /api/reports.php      (PDF/CSV report generation)
    exports.py           # /api/exports.php      (official .xlsx form exports)
    blotter_import.py    # /api/blotter_import.php
    users.py             # /api/users.php
    settings.py          # /api/settings.php     (settings, ML model, backups)
    notifications.py     # /api/notifications.php
    ml_proxy.py          # /api/ml_proxy.php     (proxies to ml/service.py)
frontend/              # the original HTML/CSS/JS, served as-is
ml/                    # the prediction microservice (see below)
seed.py                # creates tables + zones + settings + 5 demo accounts
wsgi.py                # entrypoint for gunicorn / hosting platforms
Procfile               # `web: gunicorn wsgi:app`
render.yaml             # one-click Render blueprint (web service + Postgres)
test_api.py, test_edge_cases.py, test_phase2.py   # smoke tests
```

## Run it locally

```bash
pip install -r requirements.txt
python seed.py                 # creates instance/blottercast.db (SQLite) + demo accounts
python run_dev.py              # http://localhost:5000
```

Open `http://localhost:5000/login.html` and sign in with `admin` / `admin123`
(or any of the other demo accounts).

By default this uses **SQLite** (zero setup). To use PostgreSQL locally too,
set `DATABASE_URL` before running `seed.py`:

```bash
export DATABASE_URL=postgresql://user:pass@localhost:5432/blottercast
python seed.py
python run_dev.py
```

### Email OTP (multi-factor authentication)

Every login requires a 6-digit code emailed to the account, in addition to
the password — this applies to **all accounts**, there's no toggle to turn
it off. If `SMTP_HOST` isn't set, codes aren't actually emailed: they're
written to `instance/otp_outbox.log` instead, so the app still runs
end-to-end without real mail credentials. That's fine for local dev and is
what the test suite relies on — open that file after logging in to read the
code. For anything real users will touch, set these in the environment
(any standard SMTP provider works — Gmail app password, SendGrid, Mailgun,
Amazon SES SMTP, your host's relay, etc.):

```bash
export SMTP_HOST=smtp.example.com
export SMTP_PORT=587
export SMTP_USER=your-smtp-username
export SMTP_PASSWORD=your-smtp-password
export SMTP_FROM="BlotterCast <no-reply@yourdomain.example>"
```

Every account needs a real email on file — `seed.py` gives the demo
accounts `<username>@blottercast.local` addresses, and the Users page now
requires one when creating or editing an account (no email, no way to
receive the code, no login). Codes expire after 5 minutes, allow 5 wrong
guesses before requiring a resend, and resends are rate-limited to one per
30 seconds. See `MFA_CODE_EXPIRY_MINUTES` / `MFA_MAX_ATTEMPTS` /
`MFA_RESEND_COOLDOWN_SECONDS` in `.env.example` to change any of that.

### Running the ML prediction service

The Predictions page needs `ml/service.py` running. It auto-starts itself
the first time you open that page (same as the original — the app spawns it
in the background), but you can also run it manually:

```bash
pip install -r ml/requirements.txt
python ml/service.py           # listens on :5001
```

It reads from the **same** `DATABASE_URL` as the main app (I updated it from
its original direct MySQL/pymysql connection to SQLAlchemy, so it now shares
one database instead of needing a second one).

## Deploy it (hosted, with PostgreSQL)

**Render** (easiest): push this folder to a GitHub repo, then in Render
click **New → Blueprint** and point it at the repo — `render.yaml` provisions
a free Postgres database and a web service automatically.

Any host works the same way — it just needs:
- `DATABASE_URL` — a Postgres connection string
- `SECRET_KEY` — any random string (session-signing key)
- `SESSION_COOKIE_SECURE=1` once you're on HTTPS
- `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM` — required for login to actually work for anyone but you, since MFA codes need somewhere real to go (see above)
- Start command: `gunicorn wsgi:app`
- One-time: run `python seed.py` against the production `DATABASE_URL`

The ML service (`ml/service.py`) is a separate process — on most hosts
you'll want it as its own worker/service (pointed at the same
`DATABASE_URL`), rather than relying on the auto-spawn-in-background trick,
since many PaaS platforms don't allow a web dyno to launch a second
long-running process.

## What changed vs. the PHP version (behavior-preserving)

- **Sessions:** Flask's signed cookie session instead of PHP's `session_start()`. Same idle-timeout, same forced password-change flag.
- **Passwords:** `bcrypt`, same hash format PHP's `password_hash()` uses.
- **Dates:** SQLite requires real `date`/`time` objects rather than raw strings (MySQL didn't care) — handled by `parse_date`/`parse_time` in `helpers.py`. No effect on the API contract.
- **Database backups:** now a portable INSERT-statement dump (works on SQLite or Postgres) instead of a MySQL-specific `SHOW CREATE TABLE` dump.
- **ML service:** now reads/writes via SQLAlchemy against the shared `DATABASE_URL` instead of a separate direct MySQL connection.
- **Login:** the original was password-only. This version adds mandatory email OTP as a second factor — see "Email OTP" above.

## Testing

```bash
python test_api.py            # login (incl. MFA), RBAC, census/blotter/clearance happy path
python test_edge_cases.py     # duplicate residents, same-person blotter, permission 403s
python test_phase2.py         # analytics, reports, exports, users, settings, notifications, import
python test_mfa.py            # OTP: happy path, wrong/expired codes, attempt limit, resend cooldown, no-email rejection
python test_extra_coverage.py # password change, session-timeout expiry, signature upload/removal, auto-backup scheduling
python test_ml_proxy.py       # ml_proxy blueprint against a REAL ml/service.py subprocess (auto-spawn, RBAC, forwarding)
python test_reports_matrix.py # every report type x format (pdf/excel) actually generates and downloads
python test_users_fields.py   # confirms users.php field names match exactly what frontend/users.html sends
```

All of these pass end-to-end against a fresh seeded database — SQLite or
Postgres (see "Run it locally" above for switching). `test_mfa_helper.py`
is a shared helper the other scripts import to complete the two-step login
(it reads the OTP back out of `instance/otp_outbox.log`, the same dev
fallback described above) — it isn't a test on its own.

`test_ml_proxy.py` and `test_reports_matrix.py` take longer (the former
actually trains real scikit-learn models; give it up to ~90s).
