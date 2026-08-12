"""
ResuMind AI Launcher
Starts the FastAPI backend and the Streamlit frontend together.

The app needs BOTH processes running: the Streamlit UI refuses to show the
upload form unless it can reach the backend's /health endpoint. Starting only
`streamlit run app.py` is the most common reason analysis appears to do nothing.

Usage:
    python run.py
"""

import os
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

ROOT = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
API_PORT = int(os.getenv("RESUMIND_API_PORT", "8000"))
UI_PORT = int(os.getenv("RESUMIND_UI_PORT", "8501"))
API_URL = f"http://localhost:{API_PORT}"


def wait_for_api(timeout: int = 90) -> bool:
    """Poll the backend health endpoint until it responds or we give up."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(f"{API_URL}/health", timeout=2) as response:
                if response.status == 200:
                    return True
        except (URLError, OSError):
            time.sleep(1)
    return False


def main() -> int:
    env = os.environ.copy()
    env["RESUMIND_API_URL"] = API_URL

    print(f"Starting backend on {API_URL} ...")
    backend = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", str(API_PORT)],
        cwd=ROOT,
        env=env,
    )
    frontend = None

    try:
        if not wait_for_api():
            print("ERROR: backend failed to start. Check the log output above.")
            backend.terminate()
            return 1

        print(f"Backend is healthy. Starting UI on http://localhost:{UI_PORT} ...")
        frontend = subprocess.Popen(
            [PYTHON, "-m", "streamlit", "run", "app.py",
             "--server.port", str(UI_PORT)],
            cwd=ROOT,
            env=env,
        )

        # Exit as soon as either process dies so we never leave a half-running app.
        while True:
            if backend.poll() is not None:
                print("Backend exited; shutting down UI.")
                frontend.terminate()
                break
            if frontend.poll() is not None:
                print("UI exited; shutting down backend.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down ...")
    finally:
        for proc in (frontend, backend):
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
