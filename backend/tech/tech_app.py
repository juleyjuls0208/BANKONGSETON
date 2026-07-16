"""
Bangko ng Seton — Tech / Admin Kiosk
====================================

A standalone terminal for hardware and card-lifecycle work, kept SEPARATE from
the finance dashboard and from the loading kiosk. Its job:

  * RFID reader debugging (connect serial, raw card read, UID validation)
  * Register a NEW money card for a student (ID card + money card tap)
  * Report a lost card, and issue a REPLACEMENT card (balance transfer)

It reuses the exact same RFID reading + card-linking handlers as the on-prem
admin tool (via dashboard_core.register_routes(..., modes=("hardware",))), so
behaviour never drifts. Balance writes still go through services.loading_service.

This app is meant to run on a dedicated on-prem machine wired to the Arduino
(RFID reader), so it is hardware-enabled by design.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, request, session, url_for
from flask_cors import CORS
from flask_socketio import SocketIO

load_dotenv()

sys_path = os.path.join(os.path.dirname(__file__), "..")
import sys as _sys
if sys_path not in _sys.path:
    _sys.path.insert(0, sys_path)
_dash_path = os.path.join(sys_path, "dashboard")
if _dash_path not in _sys.path:
    _sys.path.insert(0, _dash_path)

try:
    from errors import get_logger
    logger = get_logger(__name__)
except Exception:
    logger = logging.getLogger(__name__)

from sheets_adapter import APIError, SpreadsheetNotFound, WorksheetNotFound

# Startup guards (mirror dashboard).
_secret_key = os.getenv("FLASK_SECRET_KEY", "").strip()
_INSECURE = "bangko-admin-secret-key-change-in-production"
if not _secret_key or _secret_key == _INSECURE:
    logger.critical("event=startup_aborted reason=insecure_secret_key")
    raise SystemExit(1)
_jwt_secret = os.getenv("JWT_SECRET", "").strip()
_JWT_INSECURE = "bangko-jwt-secret-2026"
if not _jwt_secret or _jwt_secret == _JWT_INSECURE:
    logger.critical("event=startup_aborted reason=insecure_jwt_secret")
    raise SystemExit(1)
if (os.environ.get("WEB_CONCURRENCY", "1") not in ("", "1")
        or os.environ.get("GUNICORN_WORKERS", "1") not in ("", "1")):
    logger.critical("event=startup_aborted reason=multi_worker_forbidden")
    raise SystemExit(1)

TECH_USERNAME = os.getenv("TECH_USERNAME", os.getenv("ADMIN_USERNAME", "admin"))
TECH_PASSWORD = os.getenv("TECH_PASSWORD", os.getenv("ADMIN_PASSWORD", "admin2025"))

UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")

app = Flask(__name__)
app.secret_key = _secret_key
_cors = os.getenv("CORS_ORIGINS", "").strip()
_origins = [o.strip() for o in _cors.split(",") if o.strip()] or "*"
CORS(app, origins=_origins)
socketio = SocketIO(app, cors_allowed_origins=_origins, async_mode="threading")

db = None
try:
    from sheets_adapter import get_sheets_client
    db = get_sheets_client()
except Exception as e:  # offline/dev
    logger.warning("event=tech_db_unavailable error=%s", e)

# Register ONLY the hardware/RFID + card-lifecycle routes from the shared core.
from dashboard_core import register_routes, get_cors_origins
register_routes(app, socketio, modes=("hardware",))


# ---------------------------------------------------------------------------
# Auth (tech operator only)
# ---------------------------------------------------------------------------

def tech_login_required(f):
    @wraps(f)
    def _w(*a, **k):
        if "tech_logged_in" not in session:
            return redirect(url_for("tech_login"))
        return f(*a, **k)
    return _w


@app.route("/tech/login", methods=["GET", "POST"])
def tech_login():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        u = data.get("username"); p = data.get("password")
        if u == TECH_USERNAME and p == TECH_PASSWORD:
            session["tech_logged_in"] = True
            session["tech_username"] = u
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    from flask import send_from_directory
    return send_from_directory(os.path.join(os.path.dirname(__file__), "static"), "tech_login.html")


@app.route("/tech/logout", methods=["POST"])
def tech_logout():
    session.pop("tech_logged_in", None)
    return jsonify({"success": True})


@app.route("/tech/", methods=["GET"])
@tech_login_required
def tech_home():
    from flask import send_from_directory
    return send_from_directory(os.path.join(os.path.dirname(__file__), "static"), "tech.html")


@app.route("/api/tech/health", methods=["GET"])
def tech_health():
    db_ok = bool(db) and db.test_connection()
    return jsonify({"service": "tech-kiosk", "status": "ok", "db": db_ok})


# Thin wrappers that require tech login for the shared hardware endpoints.
@app.route("/api/tech/serial/connect", methods=["POST"])
@tech_login_required
def tech_serial_connect():
    # Delegate to the shared connect_serial handler.
    from dashboard_core import card_reader_state
    data = request.get_json(silent=True) or {}
    port = data.get("port") or os.getenv("SERIAL_PORT", "COM3")
    try:
        import serial
        from arduino_bridge import ArduinoBridge
    except Exception as e:
        return jsonify({"success": False, "error": f"Hardware unavailable: {e}"}), 400
    try:
        ser = serial.Serial(port, int(data.get("baud_rate", 9600)), timeout=1)
        card_reader_state.set("arduino", ser)
        bridge = ArduinoBridge(ser, socketio)
        app.arduino_bridge = bridge
        bridge.start_background_listener()
        return jsonify({"success": True, "message": "connected"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/tech/rfid/read", methods=["POST"])
@tech_login_required
def tech_rfid_read():
    """Trigger a raw RFID read for debugging; returns the UID via SocketIO."""
    from dashboard_core import card_reader_state
    ard = card_reader_state.get("arduino")
    if not ard or not ard.is_open:
        return jsonify({"error": "Arduino not connected"}), 400
    # Reuse the dashboard's read thread in a debug (no-link) mode.
    card_reader_state.set("card_reading_active", True)
    socketio.emit("status", {"type": "info", "message": "Waiting for card (debug)..."})
    threading.Thread(target=_debug_read_card, daemon=True).start()
    return jsonify({"success": True})


def _debug_read_card():
    from dashboard_core import card_reader_state
    import time as _t
    ard = card_reader_state.get("arduino")
    start = _t.time()
    while card_reader_state.get("card_reading_active") and _t.time() - start < 15:
        try:
            if ard and ard.in_waiting > 0:
                line = ard.readline().decode("utf-8", errors="ignore").strip()
                if line.startswith("CARD|"):
                    uid = line[5:]
                    ok = bool(UID_PATTERN.match(uid))
                    socketio.emit("rfid_debug", {"uid": uid, "valid": ok})
                    card_reader_state.set("card_reading_active", False)
                    return
        except Exception as e:
            logger.error("event=tech_debug_read_error error=%s", exc_info=True)
            socketio.emit("rfid_debug", {"uid": None, "error": str(e)})
            return
        _t.sleep(0.05)
    card_reader_state.set("card_reading_active", False)
    socketio.emit("rfid_debug", {"uid": None, "timeout": True})


if __name__ == "__main__":
    port = int(os.getenv("TECH_PORT", "5004"))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
