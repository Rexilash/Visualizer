import shutil
import subprocess
import sys

# Dynamically resolve flutter binary path
flutter_cmd = shutil.which("flutter") or "/home/rexilash/flutter/flutter/bin/flutter"

# Spawn backend process
backend = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.server:app", "--reload", "--port", "8000"]
)

try:
    # Run Flutter frontend
    subprocess.run([flutter_cmd, "run", "-d", "linux"], cwd="frontend")
finally:
    # Clean up backend process when Flutter closes
    backend.terminate()