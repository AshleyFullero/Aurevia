#!/usr/bin/env python3
"""
Aurevia Backend — Development startup helper.

Usage:
    python run.py           — Start the dev server (with auto-reload)
    python run.py seed      — Seed the database with demo data
    python run.py test      — Run the test suite
    python run.py test -v   — Run tests with verbose output + coverage
"""
from __future__ import annotations

import subprocess
import sys
import os

# Ensure we run from the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def run_server():
    """Start the Uvicorn development server with hot reload."""
    print("🚀 Starting Aurevia API server...")
    print("   Docs:   http://localhost:8000/docs")
    print("   ReDoc:  http://localhost:8000/redoc")
    print("   Health: http://localhost:8000/health\n")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info",
    ])


def run_seed():
    """Seed the database with demo data."""
    print("🌱 Seeding the database...")
    subprocess.run([sys.executable, "seed_data.py"])


def run_tests(extra_args: list[str] | None = None):
    """Run the pytest test suite."""
    args = [sys.executable, "-m", "pytest"]
    if extra_args:
        args.extend(extra_args)
    else:
        args.extend(["--cov=app", "--cov-report=term-missing"])
    subprocess.run(args)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "server"
    extra = sys.argv[2:] if len(sys.argv) > 2 else None

    if command == "seed":
        run_seed()
    elif command == "test":
        run_tests(extra)
    elif command in ("server", "dev", "start"):
        run_server()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
