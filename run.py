"""
run.py — Development Entry Point
=================================
For local development only.
Production: gunicorn "app:create_app('production')" --bind 0.0.0.0:8000 --workers 4
"""
import os
import socket
from app import create_app

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    try:
        ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        ip = "127.0.0.1"

    print(f"\n{'='*54}")
    print(f"  UttarCheck — Running!")
    print(f"{'='*54}")
    print(f"  Laptop : http://localhost:5000")
    print(f"  Phone  : http://{ip}:5000   ← same WiFi")
    print(f"  Health : http://localhost:5000/health")
    print(f"  Model  : {app.config['MODEL_NAME']}")
    print(f"  Backend: {app.config['INFERENCE_BACKEND']}")
    print(f"  Pillow : {app.config['USE_PILLOW']}")
    print(f"{'='*54}\n")

    if not app.config.get("GEMMA_API_KEY"):
        print("  ⚠️  GEMMA_API_KEY missing in .env!\n")

    app.run(host="0.0.0.0", port=5000, debug=False)