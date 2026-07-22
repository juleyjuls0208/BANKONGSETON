"""Build double-click Windows executables for the two on-prem apps.

Targets:
  - Cashier app        (backend/cashier_app/app.py        -> port 5010)
  - Registration panel (backend/dashboard/registration_app.py -> port 5004)

Output is PyInstaller ONE-FOLDER (a dist/<name>/ dir containing <name>.exe plus
the bundled .env, credentials.json, templates/, static/). The school machine
needs no Python install: copy the dist/<name> folder to the lab PC and
double-click <name>.exe.

Why one-folder (not one-file): a frozen Flask app resolves templates/static
relative to the executable, and the apps load .env + Google credentials.json at
runtime. One-folder lets us drop those assets next to the exe so the same path
logic the dev server uses keeps working. One-file would hide them in a temp
dir and complicate the runtime file reads.

Usage:
    ..\\.venv\\Scripts\\python.exe build_exes.py            # build both
    ..\\.venv\\Scripts\\python.exe build_exes.py cashier    # build one
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
CRED_SRC = ROOT / "backend" / "dashboard" / "credentials.json"
ENV_SRC = ROOT / ".env"

# name -> (entry script, app templates dir, app static dir or None, extra hidden imports)
# The entry's OWN directory is added to --paths automatically below; the extra
# list covers sibling modules the app imports via try/except (PyInstaller's
# analyzer can miss those because the first relative-import attempt raises).
TARGETS = {
    "cashier_app": {
        "entry": ROOT / "backend" / "cashier_app" / "app.py",
        "templates": ROOT / "backend" / "cashier_app" / "templates",
        "static": ROOT / "backend" / "cashier_app" / "static",
        "hidden": ["cashier_routes", "dashboard.arduino_bridge"],
    },
    "registration_app": {
        "entry": ROOT / "backend" / "dashboard" / "registration_app.py",
        "templates": ROOT / "backend" / "dashboard" / "templates",
        "static": ROOT / "backend" / "dashboard" / "static",
        "hidden": ["dashboard_core", "offline_queue", "sheets_adapter", "notifications"],
    },
}


def build_one(name: str, cfg: dict) -> Path:
    out_dir = ROOT / "dist" / name
    entry_dir = cfg["entry"].parent
    cmd = [
        str(VENV_PY), "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onedir", "--name", name,
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build" / "specs"),
        # backend/ is on sys.path in dev; the entry's own dir is where its
        # sibling modules live (cashier_routes, dashboard_core, ...). Frozen,
        # __file__ sits at dist/<name>/<name>.exe so the app's own sys.path
        # math no longer points here -> add it explicitly.
        "--paths", str(ROOT / "backend"),
        "--paths", str(entry_dir),
        # common backend modules pulled in via runtime sys.path tricks / lazy imports
        "--hidden-import", "engineio",
        "--hidden-import", "socketio",
        # Flask-SocketIO picks an async_mode at runtime by importing one of these
        # lazily; PyInstaller can't see the lazy import, so the frozen exe dies
        # with "Invalid async_mode specified". The threading driver is enough for
        # a desktop click-to-run app (no eventlet/gevent needed).
        "--hidden-import", "engineio.async_drivers.threading",
        "--hidden-import", "simple_websocket",
    ]
    for mod in cfg["hidden"]:
        cmd += ["--hidden-import", mod]
    for asset_name in ("templates", "static"):
        asset_path = cfg.get(asset_name)
        if asset_path and asset_path.exists():
            cmd += ["--add-data", f"{asset_path}{os.pathsep}{asset_name}"]
    cmd.append(str(cfg["entry"]))
    print(f"\n=== building {name} ===", flush=True)
    subprocess.run(cmd, check=True)

    # --- drop runtime assets next to the exe so Flask path logic holds ---
    exe_dir = out_dir  # onedir: <name>.exe sits directly in dist/<name>/
    # Flask resolves static files beside the frozen EXE, not from PyInstaller's
    # _internal data folder. Keep the browser-served copy there.
    if cfg.get("static") and cfg["static"].exists():
        shutil.copytree(cfg["static"], exe_dir / "static", dirs_exist_ok=True)
    if ENV_SRC.exists():
        shutil.copy2(ENV_SRC, exe_dir / ".env")
    if CRED_SRC.exists():
        # bundle credentials.json at every path the resolvers probe:
        #  - cwd (PyInstaller sets cwd to exe dir on double-click)
        #  - <exe_dir>/backend/credentials.json  (cashier's BACKEND_DIR probe)
        #  - <exe_dir>/config/credentials.json   (dashboard_core's ../../config probe)
        for dest in (exe_dir / "credentials.json",
                     exe_dir / "backend" / "credentials.json",
                     exe_dir / "config" / "credentials.json"):
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(CRED_SRC, dest)

    # --- click-to-run wrapper that launches the exe and opens the browser ---
    port = "5010" if name == "cashier_app" else "5004"
    bat = exe_dir / f"Start {name.split('_')[0].capitalize()}.bat"
    bat.write_text(
        "@echo off\n"
        "cd /d \"%~dp0\"\n"
        f'start "" /b "{name}.exe"\n'
        "timeout /t 3 /nobreak\n"
        f'start "" "http://localhost:{port}/"\n',
        encoding="utf-8",
    )
    print(f"=== {name} built -> {exe_dir / (name + '.exe')} ===", flush=True)
    return exe_dir


def main() -> int:
    aliases = {"cashier": "cashier_app", "registration": "registration_app"}
    wanted = [aliases.get(arg, arg) for arg in sys.argv[1:]]
    names = [n for n in TARGETS if n in wanted] if wanted else list(TARGETS)
    for name in names:
        build_one(name, TARGETS[name])
    # quick distro note
    note = ROOT / "dist" / "README.txt"
    note.write_text(
        "Bangko ng Seton - on-prem executables\n"
        "=====================================\n\n"
        "Each subfolder is a self-contained app. No Python install needed.\n"
        "Copy the whole subfolder to the lab PC, then double-click the .exe\n"
        "(or the 'Start <App>.bat' wrapper to also auto-open the browser).\n\n"
        "  cashier_app/        -> http://localhost:5010  (cashier POS)\n"
        "  registration_app/   -> http://localhost:5004  (on-prem card reader panel)\n\n"
        "Keep .env and credentials.json next to the .exe (already bundled).\n"
        "To update: re-run build_exes.py and copy the regenerated folder over.\n",
        encoding="utf-8",
    )
    print("\nDone. See dist/README.txt", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
