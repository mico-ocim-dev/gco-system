# GCO System – Hosting Tutorial

This tutorial shows how to put the GCO Office Management System online so it can be used from anywhere. You can choose one of the options below depending on what you prefer (free tier, simplicity, or full control).

**👉 First time?** Use **[HOSTING_CHECKLIST.md](HOSTING_CHECKLIST.md)** for the full “what you need to do” list (tech stack, host, domain, database, upload, security, testing).

---

## Table of contents

1. [Before you start](#1-before-you-start)
2. [Option A: Railway (recommended for beginners)](#option-a-railway-recommended-for-beginners)
3. [Option B: Render](#option-b-render)
4. [Option C: PythonAnywhere](#option-c-pythonanywhere)
5. [Option D: VPS (Ubuntu server)](#option-d-vps-ubuntu-server)
6. [After deployment](#6-after-deployment)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Before you start

### What you need

- The GCO System project (this folder) in a **Git repository** (e.g. GitHub, GitLab).
- A **SECRET_KEY** for production. Generate one on your computer:

  **Windows (Command Prompt or PowerShell):**
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
  Copy the long string that appears (e.g. `a1b2c3d4e5...`). You will use it as `SECRET_KEY` on the host.

### What the app needs on the host

| Variable       | What to set |
|----------------|-------------|
| **SECRET_KEY** | The long random string you generated above. |
| **DATABASE_URL** | A database URL (PostgreSQL or MySQL). Many hosts create this for you when you add a database. |
| **PORT**       | Often set automatically by the host. Only set if the host tells you to. |

If you do **not** set `DATABASE_URL`, the app will use SQLite. On free hosting this is usually not recommended because the file system may be reset. Use a hosted database (PostgreSQL/MySQL) when the host offers it.

---

## Option A: Railway (recommended for beginners)

Railway gives you a free tier with PostgreSQL and automatic deploys from GitHub.

### Step 1: Push your code to GitHub

1. Create a new repository on [GitHub](https://github.com) (e.g. `gco-system`).
2. **If Git is not installed:** Download from https://git-scm.com/download/win and install, then close and reopen Command Prompt.
3. **First-time only – set your Git identity** (use the name and email for your GitHub account). Run these once:

   ```
   git config --global user.name "Mico Rosales"
   git config --global user.email "mico.rosales@lspu.edu.ph"
   ```

4. Open Command Prompt and go to your project folder. **Do NOT type the word "bash" or any backticks.** Run each line below, one at a time (press Enter after each):

   ```
   cd "C:\Users\ASUS\OneDrive\Desktop\GCO System"
   git init
   git add .
   git commit -m "Initial commit - GCO System"
   git branch -M main
   git remote add origin https://github.com/mico-ocim-dev/gco-system.git
   git push -u origin main
   ```

   If you see "remote origin already exists", run instead: `git remote set-url origin https://github.com/mico-ocim-dev/gco-system.git` then run `git push -u origin main`.

   Use your real GitHub username in the URL (no spaces).

### Step 2: Create a Railway project

1. Go to [railway.app](https://railway.app) and sign in (e.g. with GitHub).
2. Click **“New Project”**.
3. Choose **“Deploy from GitHub repo”** and select your `gco-system` repository.
4. Railway will add a service for your app. Do not add a database yet; we will add it in the next step.

### Step 3: Add a PostgreSQL database

1. In the same project, click **“New”** → **“Database”** → **“PostgreSQL”**.
2. Wait until the database is created. Click the PostgreSQL service.
3. Open the **“Variables”** or **“Connect”** tab and copy the **`DATABASE_URL`** (it looks like `postgresql://postgres:xxxxx@host:5432/railway`).

### Step 4: Set environment variables for your app

1. Click your **app service** (the one from GitHub), not the database.
2. Go to **“Variables”** (or **Settings → Variables**).
3. Click **“Add Variable”** or **“RAW Editor”** and add:

   ```
   SECRET_KEY=paste_your_long_secret_key_here
   DATABASE_URL=paste_the_database_url_from_postgres_service
   ```

   Paste the real values (no quotes needed). Railway may already add `DATABASE_URL` if you linked the database to the app; if so, only add `SECRET_KEY`.

   **(Optional) Gmail verification:** To require new users to verify their Gmail before they can log in, add these variables (use a Gmail account and an [App Password](https://support.google.com/accounts/answer/185833)):

   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=1
   MAIL_USERNAME=your-gmail@gmail.com
   MAIL_PASSWORD=your_app_password
   MAIL_DEFAULT_SENDER=your-gmail@gmail.com
   ```

   If you do not set `MAIL_SERVER`, new users can log in without verifying their email.

### Step 5: Add production dependencies (if not already in requirements.txt)

The project already includes a **Procfile** that tells Railway how to start the app. You only need to add the production packages to **requirements.txt** (add or uncomment these lines):

   ```
   gunicorn>=21.0.0
   psycopg2-binary>=2.9.0
   ```

3. Commit and push:

   ```bash
   git add requirements.txt
   git commit -m "Add production deps for Railway"
   git push
   ```

Railway will redeploy automatically. When it finishes, open the URL Railway gives you (e.g. `https://your-app.up.railway.app`).

### Step 6: First login

- Go to your app URL and open the **Login** page.
- Log in with **Email** `admin@gco.lspu.edu.ph`, **Password** `admin123`.
- Change the admin password immediately (e.g. in profile or user management if you add it, or by updating the database).
- **Note:** Users sign in with **email and password**. New users register with a Gmail address; if you set `MAIL_SERVER` in Step 4, they must click the verification link sent to their Gmail before they can log in.

---

## Option B: Render

Render has a free tier and can host Flask apps with a PostgreSQL database.

### Step 1: Push code to GitHub

Same as Railway: have your GCO System in a GitHub repository.

### Step 2: Create a Web Service on Render

1. Go to [render.com](https://render.com) and sign in (e.g. with GitHub).
2. Click **“New +”** → **“Web Service”**.
3. Connect your GitHub account if needed and select the `gco-system` repository.
4. Use these settings:
   - **Name:** `gco-system` (or any name).
   - **Environment:** `Python 3`.
   - **Build Command:** `pip install -r requirements.txt`  
     (If you added gunicorn and psycopg2-binary to requirements.txt, that’s enough.)
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:$PORT "app:app"`.

### Step 3: Add a PostgreSQL database

1. In the Render dashboard, click **“New +”** → **“PostgreSQL”**.
2. Create the database and note the **Internal Database URL** (or **External** if you prefer; use one consistently).
3. Copy that URL; you will add it to the Web Service as `DATABASE_URL`.

### Step 4: Set environment variables

1. Open your **Web Service** → **Environment**.
2. Add:
   - **SECRET_KEY** = your generated secret key.
   - **DATABASE_URL** = the PostgreSQL URL from the database you created.

Click **Save Changes**. Render will redeploy.

### Step 5: Dependencies

Ensure **requirements.txt** includes:

```
gunicorn>=21.0.0
psycopg2-binary>=2.9.0
```

Push to GitHub if you changed it. First login: `admin` / `admin123` (then change the password).

---

## Option C: PythonAnywhere

Good for learning; free tier has some limits (e.g. one app, restricted outbound ports). You can use SQLite here if you want to keep it simple.

### Step 1: Create an account

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com) and register (free account is enough).

### Step 2: Upload your project

1. Open the **Files** tab and go to your user directory (e.g. `/home/yourusername`).
2. Upload your project (e.g. as a zip, then unzip, or use **Git clone** in the **Consoles** tab):

   ```bash
   git clone https://github.com/YOUR_USERNAME/gco-system.git
   cd gco-system
   ```

### Step 3: Create a virtualenv and install dependencies

1. In **Consoles** → **Bash**, go to the project folder:
   ```bash
   cd ~/gco-system
   ```
2. Create and use a virtualenv, then install packages (add psycopg2-binary if you use PostgreSQL later):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

### Step 4: Web app configuration

1. Open the **Web** tab and click **“Add a new web app”**.
2. Choose **“Manual configuration”** (not Django) and **Python 3.10** (or the version shown).
3. In **“Code”**:
   - **Source code:** `/home/yourusername/gco-system`
   - **Working directory:** `/home/yourusername/gco-system`
4. In **“WSGI configuration file”**, click the link to edit the WSGI file. Replace its contents with something like (adjust `yourusername`):

   ```python
   import sys
   path = '/home/yourusername/gco-system'
   if path not in sys.path:
       sys.path.insert(0, path)

   from app import app as application
   ```

5. **Virtualenv:** Set to `/home/yourusername/gco-system/venv`.

### Step 5: Environment variables

In the **Web** tab, find **“Environment variables”** (or add them in the WSGI file before `from app import app`):

```python
import os
os.environ["SECRET_KEY"] = "your-long-secret-key-here"
# Optional, for SQLite leave DATABASE_URL unset:
# os.environ["DATABASE_URL"] = "postgresql://..."
```

Reload the web app. Your site will be at `https://yourusername.pythonanywhere.com`. First login: `admin` / `admin123`.

---

## Option D: VPS (Ubuntu server)

Use this if you have a cloud server (e.g. from DigitalOcean, Linode, AWS EC2, or a school server) with Ubuntu.

### Step 1: Connect to the server

```bash
ssh root@your-server-ip
# or: ssh ubuntu@your-server-ip
```

### Step 2: Install Python, PostgreSQL, and Nginx

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql nginx
```

### Step 3: Create a database and user (PostgreSQL)

```bash
sudo -u postgres psql
```

In the `postgres` prompt:

```sql
CREATE USER gco WITH PASSWORD 'your_secure_password';
CREATE DATABASE gco_db OWNER gco;
\q
```

Note: `your_secure_password` will go inside `DATABASE_URL`.

### Step 4: Upload your project

From your **local** machine (in the project folder):

```bash
scp -r "C:\Users\ASUS\OneDrive\Desktop\GCO System" ubuntu@your-server-ip:/home/ubuntu/gco-system
```

Or clone from GitHub on the server:

```bash
cd /home/ubuntu
git clone https://github.com/YOUR_USERNAME/gco-system.git
cd gco-system
```

### Step 5: Virtualenv and dependencies

On the **server**:

```bash
cd /home/ubuntu/gco-system
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Step 6: Environment variables

Create a file that will load your environment (do not commit this file):

```bash
nano /home/ubuntu/gco-system/.env
```

Add (use your real values):

```
SECRET_KEY=your_long_secret_key_here
DATABASE_URL=postgresql://gco:your_secure_password@localhost:5432/gco_db
FLASK_DEBUG=0
```

To load this in the app you can use `python-dotenv` (add to requirements and load in `config.py`) or export them before running:

```bash
export $(cat .env | xargs)
```

### Step 7: Run with Gunicorn (test)

```bash
cd /home/ubuntu/gco-system
source venv/bin/activate
export $(cat .env | xargs)
gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
```

Visit `http://your-server-ip:5000`. If it works, press Ctrl+C and set up Nginx + a process manager next.

### Step 8: Gunicorn as a systemd service

Create a service file:

```bash
sudo nano /etc/systemd/system/gco.service
```

Paste (adjust paths and user if needed):

```ini
[Unit]
Description=GCO System
After=network.target postgresql.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/gco-system
Environment="PATH=/home/ubuntu/gco-system/venv/bin"
EnvironmentFile=/home/ubuntu/gco-system/.env
ExecStart=/home/ubuntu/gco-system/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "app:app"
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gco
sudo systemctl start gco
sudo systemctl status gco
```

### Step 9: Nginx as reverse proxy

```bash
sudo nano /etc/nginx/sites-available/gco
```

Add (replace `your-domain.com` or use your server IP):

```nginx
server {
    listen 80;
    server_name your-domain.com;   # or your_server_ip;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/gco /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Then open `http://your-domain.com` or `http://your-server-ip`. First login: `admin` / `admin123`.

---

## 6. After deployment

- **First login:** Username `admin`, password `admin123`. Change this password as soon as possible (e.g. add a “Change password” feature or update the user in the database).
- **HTTPS:** On Railway and Render you get HTTPS by default. On a VPS, use Let’s Encrypt (e.g. `certbot`) with Nginx to get a free SSL certificate.
- **Backups:** For PostgreSQL/MySQL, use your host’s backup feature or run periodic `pg_dump` / `mysqldump` and store the file safely.
- **Uploads:** QR images and file uploads are stored in the `uploads/` folder. On free tiers this may be erased on redeploy; for long-term storage consider moving to cloud storage (e.g. S3) later.

---

## 7. Troubleshooting

| Problem | What to try |
|--------|--------------|
| **App shows “Application error” or 503** | Check the host’s logs (Railway/Render: Logs tab; VPS: `journalctl -u gco -f`). Often the cause is a missing env var (e.g. `SECRET_KEY`, `DATABASE_URL`) or a failed `pip install`. |
| **Database connection error** | Ensure `DATABASE_URL` is set correctly and that the database service is running. For PostgreSQL, if the host gives a `postgres://` URL, the app converts it to `postgresql://`; if you set it yourself, use `postgresql://`. |
| **Static files or uploads not loading** | The app serves uploads from `uploads/`. On some hosts the filesystem is read-only or reset; then you need to use external storage (e.g. S3) and change the code to point there. |
| **Default admin login doesn’t work** | Tables are created on first run. If the database was already present and empty, restart the app once so `init_db()` runs and creates the admin user. |
| **Port or “bind” errors** | The app must listen on the port the host provides (often in `PORT`). Use `gunicorn -b 0.0.0.0:$PORT "app:app"` so it uses that port. |

---

## Quick reference

- **Generate SECRET_KEY:**  
  `python -c "import secrets; print(secrets.token_hex(32))"`
- **Procfile (Railway/Render):**  
  `web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:app"`
- **First login:**  
  `admin` / `admin123` (then change password)

For more technical details (env vars, Gunicorn, database), see **DEPLOY.md**.
