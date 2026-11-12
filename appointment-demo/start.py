"""One command for newcomers: python start.py (Python 3.12+ recommended)."""
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".venv"
PYTHON = ENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run(*arguments):
    subprocess.run([str(PYTHON), *arguments], cwd=ROOT, check=True)


if __name__ == "__main__":
    try:
        if not PYTHON.exists():
            print("1/4 · Creating an isolated Python environment…", flush=True)
            venv.EnvBuilder(with_pip=True).create(ENV)
        print("2/4 · Installing the project dependencies…", flush=True)
        run("-m", "pip", "install", "-r", "requirements.txt")
        print("3/4 · Preparing the database and demo accounts…", flush=True)
        run("manage.py", "migrate")
        run("manage.py", "seed_demo")
        print("4/4 · Open http://127.0.0.1:8000 · Stop with Ctrl+C", flush=True)
        run("manage.py", "runserver")
    except KeyboardInterrupt:
        print("\nServer stopped. Your appointments are saved.")
    except subprocess.CalledProcessError:
        print("\nSetup stopped. Read the error above; see README for manual setup.")
        sys.exit(1)
