import os
import sys
from pathlib import Path

# Setup Python path before importing backend modules
current_dir = Path(__file__).resolve().parent
candidate_dirs = [
    current_dir.parent / "backend",
    current_dir / "backend",
    Path.cwd() / "backend",
    Path("/var/task/backend"),
    Path("/var/task"),
    current_dir.parent,
    current_dir,
]

for candidate in candidate_dirs:
    if (candidate / "app" / "main.py").exists():
        p = str(candidate)
        if p not in sys.path:
            sys.path.insert(0, p)
        os.environ["PYTHONPATH"] = p
        break

root_dir = str(current_dir.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app
