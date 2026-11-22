import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set PYTHONPATH environment variable if not already present
os.environ.setdefault("PYTHONPATH", backend_dir)

# Import the FastAPI application instance
from app.main import app
