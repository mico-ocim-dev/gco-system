# ✅ WHAT YOU NEED TO DO TO HOST THE SYSTEM

Use this checklist to get the GCO Office Management System online. The system is **Flask (Python)** and works with **MySQL or PostgreSQL** on the right hosting.

---

## 🧩 1. Decide the FINAL TECH STACK (VERY IMPORTANT)

This project is **already built** with:

| Part        | This system uses      | Notes                          |
|------------|------------------------|--------------------------------|
| **Backend**| **Flask (Python)**     | Not PHP – so you need Python hosting. |
| **Database** | **SQLite** (local) or **MySQL / PostgreSQL** (hosting) | For hosting, use MySQL or PostgreSQL. |
| **Hosting** | See options below      | Shared PHP hosts (Hostinger cPanel, etc.) run PHP, not Python. |

### ✅ OPTION A – EASIEST (Recommended for students / non-technical)

**Flask + PostgreSQL + Railway or Render (free tier)**

- No cPanel; you use their web dashboard.
- They give you: app URL, database, and automatic deploy from GitHub.
- **Best for:** Getting online quickly with minimal setup.

👉 **Follow:** [HOSTING_TUTORIAL.md](HOSTING_TUTORIAL.md) → **Option A: Railway** or **Option B: Render**.

### ⚠️ OPTION B – MORE CONTROL

**Flask + MySQL (or PostgreSQL) + VPS**

- You get a server (e.g. Ubuntu), install Python, MySQL, Nginx, run the app with Gunicorn.
- **Best for:** When you need a VPS, your school has a server, or you want full control.

👉 **Follow:** [HOSTING_TUTORIAL.md](HOSTING_TUTORIAL.md) → **Option D: VPS (Ubuntu server)**.

### ❌ Why not “PHP + Shared Hosting” for this project?

- The GCO system is **written in Python (Flask)**. It cannot run on a host that only supports PHP (e.g. basic Hostinger/Bluehost shared hosting without Python).
- To use **Hostinger, Bluehost, GoDaddy** you would need either:
  - A plan that supports **Python** (e.g. VPS or “Python app” if they offer it), or
  - A **different project** built in PHP (Laravel) – that would be a separate rewrite.

**👉 If your client is non-technical, use Option A (Railway or Render) so they get a link and don’t manage a server.**

---

## 🖥️ 2. Get a HOSTING PROVIDER (Required)

Your client (or school) must have **one** hosting solution. For **this Flask app**, use one of these:

| Host            | Best for           | Database   | Difficulty |
|-----------------|--------------------|------------|------------|
| **Railway**     | Easiest, free tier | PostgreSQL | ⭐ Easy    |
| **Render**      | Easy, free tier    | PostgreSQL | ⭐ Easy    |
| **PythonAnywhere** | Students, testing | SQLite or MySQL | ⭐ Easy |
| **VPS** (DigitalOcean, Linode, etc.) | Full control | MySQL or PostgreSQL | ⭐⭐⭐ Advanced |

**Must have:**

- Support for **Python** (and preferably **Gunicorn** or “Web app”).
- **MySQL** or **PostgreSQL** (or SQLite only for small/testing, e.g. PythonAnywhere).
- A **public URL** (and optionally a custom domain).

**Note:** Traditional shared hosting that only has **PHP + MySQL** (e.g. basic Hostinger/Bluehost cPanel) does **not** run this Flask app. Use Railway, Render, PythonAnywhere, or a VPS instead.

---

## 🌐 3. Get a DOMAIN NAME (Optional but good for professional use)

Examples:

- `guidance-lspu.online`
- `lspu-gco.com`
- Subdomain: `gco.yourdomain.com`

- **Free:** e.g. Freenom, or subdomain from host (e.g. `yourapp.railway.app`).
- **Paid:** Any registrar (GoDaddy, Namecheap, etc.).

You can go live first with the host’s default URL (e.g. `https://your-app.up.railway.app`) and add a custom domain later in the host’s dashboard.

---

## 🗄️ 4. Set up the HOSTED DATABASE (MySQL or PostgreSQL)

### If using Railway or Render

- Create a **PostgreSQL** database in the dashboard (no manual DB name/user/password needed).
- Copy the **`DATABASE_URL`** they give you (e.g. `postgresql://user:pass@host:5432/dbname`).
- Paste it into your app’s **Environment variables** as `DATABASE_URL`.

### If using a VPS or host that gives you MySQL

In the control panel or on the server:

1. Create a **MySQL database** (e.g. `gco_db`).
2. Create a **DB user** and password.
3. Assign the user to the database.
4. Note:
   - **Host** (e.g. `localhost` or the server IP)
   - **Port** (usually `3306`)
   - **Database name**
   - **Username**
   - **Password**

Then set in your app (via `.env` or environment):

```text
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE_NAME
```

Replace `USER`, `PASSWORD`, `HOST`, `DATABASE_NAME` with the values you noted.

---

## 🛠️ 5. Connect MySQL Workbench (Optional but recommended for MySQL)

If you use **MySQL** (e.g. on a VPS or shared MySQL host):

1. Open **MySQL Workbench**.
2. New connection:
   - **Host:** your server IP or DB host from the panel
   - **Port:** 3306
   - **Username** and **Password:** the DB user you created
3. **Test connection.**

This confirms the database is reachable and ready for the app.

*(For PostgreSQL on Railway/Render, you can use their dashboard or a PostgreSQL client instead.)*

---

## 🚀 6. Upload Your System to the Server

This app is **Flask (Python)**, not PHP. You do **not** upload to `public_html` like a Laravel site.

### Option A – Railway / Render

1. Put your code on **GitHub** (git push from your project folder).
2. In Railway or Render, create a **new project** and connect the GitHub repo.
3. Add environment variables:
   - `SECRET_KEY` = (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `DATABASE_URL` = (from the database you created)
4. Ensure **requirements.txt** includes: `gunicorn`, `psycopg2-binary` (PostgreSQL) or `PyMySQL` (MySQL).
5. The host uses the **Procfile** in your project to run: `gunicorn -w 4 -b 0.0.0.0:$PORT "app:app"`.
6. Deploy. Your app URL will be shown in the dashboard.

👉 Full steps: [HOSTING_TUTORIAL.md](HOSTING_TUTORIAL.md).

### Option B – VPS (e.g. Ubuntu)

1. **Upload** the project (e.g. `scp`, `rsync`, or clone from GitHub).
2. On the server: create virtualenv, install dependencies, set `SECRET_KEY` and `DATABASE_URL`.
3. Run with Gunicorn (and optionally Nginx as reverse proxy).

👉 Full steps: [HOSTING_TUTORIAL.md](HOSTING_TUTORIAL.md) → Option D: VPS.

### Option C – PythonAnywhere

1. Upload or **git clone** the project in your PythonAnywhere account.
2. Create a virtualenv and install from **requirements.txt**.
3. Configure the **Web** app (WSGI file, virtualenv path).
4. Set `SECRET_KEY` (and `DATABASE_URL` if you use MySQL).

👉 Full steps: [HOSTING_TUTORIAL.md](HOSTING_TUTORIAL.md) → Option C: PythonAnywhere.

**There is no `.env` file to edit on the server for Railway/Render** – you set variables in their dashboard. On VPS or PythonAnywhere you can use a `.env` file (and optionally `python-dotenv`).

---

## 🔐 7. Secure the System

- **HTTPS (SSL):** Railway and Render provide it by default. On a VPS, use **Let’s Encrypt** (e.g. Certbot) with Nginx.
- **Admin / security:**
  - Change the default admin password (email `admin@gco.lspu.edu.ph` / password `admin123`) immediately after first login.
  - Do **not** set `FLASK_DEBUG=1` in production.
- **Secrets:** Use a strong, random `SECRET_KEY`; never commit it to Git.
- **Database:** Use a strong DB password and keep `DATABASE_URL` only in environment variables (not in code).

---

## 📊 8. Test EVERYTHING ONLINE

Use this checklist after deployment:

| Check | What to do |
|-------|------------|
| ✔️ **Login works** | Staff can log in with email and password (admin: `admin@gco.lspu.edu.ph`; users use their Gmail after verifying if MAIL_* is set). |
| ✔️ **Forms save data** | Create a document request, appointment, ticket; confirm they appear. |
| ✔️ **CSV/Excel import** | Use Import in Document Requests, Tickets, or Logbook; confirm rows are added. |
| ✔️ **Dashboard shows live data** | Open dashboard; numbers and charts load. |
| ✔️ **Reports generate** | Generate a monthly report; download PDF/CSV/Excel. |
| ✔️ **Multiple users can access** | Log in from another browser/device; both can use the system. |
| ✔️ **Track Request (public)** | Open track request page (no login); enter a tracking number and see status. |
| ✔️ **QR / uploads** | If you use QR uploads, add one and confirm it appears on the user dashboard. |

If something fails, check the host’s **logs** (Railway/Render: Logs tab; VPS: `journalctl` or Gunicorn logs) and see [HOSTING_TUTORIAL.md](HOSTING_TUTORIAL.md) → **Troubleshooting**.

---

## Quick reference

| Item | For this GCO system |
|------|---------------------|
| **Stack** | Flask (Python) + MySQL or PostgreSQL |
| **Easy hosting** | Railway or Render (PostgreSQL) |
| **Env vars** | `SECRET_KEY`, `DATABASE_URL`; optional `PORT`, `FLASK_DEBUG=0` |
| **First login** | Email `admin@gco.lspu.edu.ph` / password `admin123` → change password immediately |
| **Detailed steps** | [HOSTING_TUTORIAL.md](HOSTING_TUTORIAL.md) |
| **Technical reference** | [DEPLOY.md](DEPLOY.md) |
