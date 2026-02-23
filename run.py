"""Run the GCO Office Management System. Suitable for local and hosting."""
import os

try:
    from app import app, init_db
except ModuleNotFoundError:
    print("ERROR: Dependencies not found. Use the virtual environment:")
    print("  venv\\Scripts\\python.exe run.py")
    print("  Or double-click start.bat")
    raise SystemExit(1)

if __name__ == "__main__":
    from config import DEBUG
    init_db()
    port = int(os.environ.get("PORT", 5000))
    # On hosting, bind to 0.0.0.0 so the app is reachable from the network
    host = "0.0.0.0" if not DEBUG else "127.0.0.1"
    print(f"Starting server at http://{host}:{port}" + (" (debug)" if DEBUG else " (production)"))
    app.run(debug=DEBUG, port=port, host=host)
