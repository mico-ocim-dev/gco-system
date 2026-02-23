# Deploying GCO System (Hosting)

The app is set up to run locally (SQLite) or on a host (PostgreSQL/MySQL).

## Environment variables (hosting)

Set these on your hosting platform (e.g. Railway, Render, Heroku, PythonAnywhere):

| Variable               | Required in production | Description |
|------------------------|------------------------|-------------|
| `SECRET_KEY`           | Yes                    | Long random string for sessions/cookies. Generate with: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL`         | Yes (for most hosts)   | Database URL. **PostgreSQL**: `postgresql://user:pass@host:5432/dbname` **MySQL**: `mysql+pymysql://user:pass@host:3306/dbname` |
| `PORT`                 | No                     | Port to run on. Many hosts set this automatically. |
| `FLASK_DEBUG`          | No                     | Set to `0` in production. |
| `MAIL_SERVER`          | No (required for Gmail verification) | SMTP server, e.g. `smtp.gmail.com`. If set, new users must verify their Gmail before logging in. |
| `MAIL_PORT`            | No                     | SMTP port, usually `587`. |
| `MAIL_USE_TLS`         | No                     | Set to `1` for TLS. |
| `MAIL_USERNAME`        | No                     | SMTP username (e.g. your Gmail). |
| `MAIL_PASSWORD`        | No                     | SMTP password (e.g. Gmail App Password). |
| `MAIL_DEFAULT_SENDER`  | No                     | Sender address shown in verification emails. |

## Local (no hosting)

- Do **not** set `DATABASE_URL` → app uses SQLite (`database/app.db`).
- Run: `python run.py` or use your start script.
- Default: http://127.0.0.1:5000

## Production run options

### Option 1: Gunicorn (Linux)

```bash
pip install gunicorn psycopg2-binary   # or PyMySQL for MySQL
gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
```

Or with `PORT` from the host:

```bash
gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} "app:app"
```

### Option 2: Built-in server (small sites)

```bash
export FLASK_DEBUG=0
export PORT=5000
python run.py
```

The app binds to `0.0.0.0` when not in debug, so it is reachable from the network.

## Database

- **SQLite** (default): no extra setup. File: `database/app.db`.
- **PostgreSQL**: install `psycopg2-binary`, set `DATABASE_URL`. Tables are created on first run (`db.create_all()`).
- **MySQL**: install `PyMySQL`, set `DATABASE_URL` with `mysql+pymysql://...`. Tables are created on first run.

## First run on host

1. Set `SECRET_KEY` and `DATABASE_URL` (and optionally `PORT`).
2. (Optional) To enable Gmail verification for new users, set `MAIL_SERVER`, `MAIL_USERNAME`, and `MAIL_PASSWORD` (see table above). Without these, new users can log in without verifying email.
3. Deploy the code and run the app (e.g. via Gunicorn or `python run.py`).
4. On first request, `init_db()` creates tables and seeds the default admin user. Log in with **email** `admin@gco.lspu.edu.ph`, **password** `admin123` — change this after first login.
5. Users log in with **email and password** (not username). New user registrations require a Gmail address; if mail is configured, they must click the verification link sent to their Gmail before they can log in.

## Uploads

File uploads (QR images, attachments) are stored in the `uploads/` folder. On some hosts you may need to use persistent storage or a cloud bucket; the app currently uses local paths under `BASE_DIR`.
