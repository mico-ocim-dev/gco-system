"""WSGI entry point for production servers (e.g. Gunicorn)."""
from app import app

# Gunicorn and other WSGI servers use: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
# Or: gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
