import shutil
import subprocess
import sys
import os
import signal

# Dynamically resolve flutter binary path
flutter_cmd = shutil.which("flutter") or "/home/rexilash/flutter/flutter/bin/flutter"

if sys.platform != "win32":
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.server:app", "--reload", "--port", "8000"],
        preexec_fn=os.setsid
    )
else:
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.server:app", "--reload", "--port", "8000"]
    )

exit_code = 0

try:
    result = subprocess.run([flutter_cmd, "run", "-d", "linux"], cwd="frontend")
    exit_code = result.returncode
except FileNotFoundError:
    print(f"\n[Error] Could not locate Flutter executable at: {flutter_cmd}")
    exit_code = 1
finally:
    print("\nShutting down backend server...")
    if sys.platform != "win32":
        try:
            # Force immediate termination of the process group
            os.killpg(os.getpgid(backend.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        backend.kill()

sys.exit(exit_code)