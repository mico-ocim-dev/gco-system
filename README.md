# GCO Office Management System

Guidance and Counseling Office – LSPU Sta. Cruz

## Tech Stack

- **Backend:** Python Flask
- **Database:** SQLite (`/database/app.db`)
- **ORM:** SQLAlchemy
- **Auth:** Flask-Login (session-based, password hashing)
- **Charts:** Chart.js

## Setup

**Easy way (recommended):** Double-click `setup.bat`, then `start.bat`

**Manual way (if python/pip not in PATH, use `py` instead):**
```bash
cd "c:\Users\ASUS\OneDrive\Desktop\GCO System"
py -3 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe run.py
```

Default admin: `admin` / `admin123`

## Features

- **Document Request & Tracking** – Create, track, import/export requests
- **Dashboard** – Live counters, status distribution, monthly trends
- **Digital Logbook** – Check-in/check-out, attendance reports
- **Help Desk** – Ticket management, assignments, import/export
- **Surveys** – Create surveys, collect responses, chart analysis
- **Monthly Reports** – Generate and download PDF reports

## Public Pages

- `/auth/login` – Staff login
- `/document-requests/track` – Track request by tracking number (no login)

## Hosting (put the app online)

1. **Start here:** **[HOSTING_CHECKLIST.md](HOSTING_CHECKLIST.md)** – What you need to do (tech stack, host, domain, database, upload, security, testing).
2. **Step-by-step:** **[HOSTING_TUTORIAL.md](HOSTING_TUTORIAL.md)** – Railway, Render, PythonAnywhere, VPS.
3. **Reference:** **DEPLOY.md** – Environment variables and run commands.
