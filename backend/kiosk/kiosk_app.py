"""
Bangko ng Seton — Loading Kiosk
================================

A dedicated, touch-screen top-up terminal. Its ONLY job is to add money to a
student's money card — fast. It separates "people just loading money" from the
finance/admin dashboard and from card-issue / lost-card work (which lives in the
tech kiosk).

Three ways to identify the student to top up:
  1. RFID money-card tap      -> Arduino sends `CARD|<uid>` over serial
  2. QR scan (cardless)       -> student shows the QR in the Bangko app; the
                                 kiosk scans it and decodes the signed student JWT
  3. Manual student lookup    -> operator types the Student ID (for staff-assisted)

After the student is identified, the operator collects cash (bill validator or
preset denomination buttons) and confirms. The actual balance write always goes
through services.loading_service.load_money — the exact same code path the
dashboard uses, so totals, the Transactions Log, and parent emails stay correct.

Hardware (bill validator + QR scanner module + RFID reader + touch screen) is
optional: the kiosk runs fully without it (manual denomination buttons + manual
student ID entry) so it can be developed and tested head-less.
"""

from __future__ import annotations

import logging
import os
import re
import secrets
import threading
import time
from functools import wraps
from math import isfinite

import jwt as _pyjwt
from dotenv import load_dotenv
from flask import Flask, jsonify, request, session
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

from services.loading_service import (
    STATION_KIOSK,
    TopupSessionStore,
    load_money,
    get_student_balance,
)

from sheets_adapter import APIError, SpreadsheetNotFound, WorksheetNotFound
from sheets_adapter import get_sheets_client as _get_kiosk_db

# Import RFID bridge + utils (best effort — hardware may be absent in dev/test).
try:
    from arduino_bridge import ArduinoBridge
    _HARDWARE_OK = True
except Exception as _imp_err:  # pragma: no cover
    logger.warning("event=kiosk_hardware_import_failed error=%s", _imp_err)
    _HARDWARE_OK = False

    class _NoOp:
        pass
    ArduinoBridge = _NoOp


def normalize_card_uid(uid):
    """Canonicalize a UID without destroying significant leading zeroes."""
    return str(uid or "").strip().upper()


# --- Startup guards (mirror dashboard) -------------------------------------
_secret_key = os.getenv("FLASK_SECRET_KEY", "").strip()
_INSECURE_DEFAULT = "bangko-admin-secret-key-change-in-production"
if not _secret_key or _secret_key == _INSECURE_DEFAULT:
    logger.critical("event=startup_aborted reason=insecure_secret_key")
    raise SystemExit(1)

_jwt_secret = os.getenv("JWT_SECRET", "").strip()
if not _jwt_secret or (_jwt_secret.lower().startswith("bangko-") and "secret-" in _jwt_secret.lower()):
    logger.critical("event=startup_aborted reason=insecure_jwt_secret")
    raise SystemExit(1)

# Kiosk unlock PIN (prevents students from poking operator-only actions).
KIOSK_UNLOCK_PIN = os.getenv("KIOSK_UNLOCK_PIN", "").strip()
if not KIOSK_UNLOCK_PIN or KIOSK_UNLOCK_PIN == "1234" or not KIOSK_UNLOCK_PIN.isdigit() or len(KIOSK_UNLOCK_PIN) < 6:
    logger.critical("event=startup_aborted reason=insecure_kiosk_unlock_pin")
    raise SystemExit(1)
# Shared secret for local cardless top-up token minting (api_server -> kiosk).
KIOSK_TOPUP_SECRET = (os.getenv("KIOSK_TOPUP_SECRET", "").strip()
                      or _jwt_secret)

UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")

app = Flask(__name__)
app.secret_key = _secret_key
_cors = os.getenv("CORS_ORIGINS", "").strip()
_origins = [o.strip() for o in _cors.split(",") if o.strip()] or "*"
CORS(app, origins=_origins)
socketio = SocketIO(app, cors_allowed_origins=_origins, async_mode="threading")

# Process-local cardless top-up session store.
topup_sessions = TopupSessionStore(ttl_seconds=int(os.getenv("KIOSK_QR_TTL", "120")))
_pending_topups: dict[str, dict] = {}
_completed_topups: dict[str, dict] = {}
_pending_topups_lock = threading.Lock()
_PENDING_TOPUP_TTL = int(os.getenv("KIOSK_TOPUP_PENDING_TTL", "120"))
_unlock_attempts: dict[str, list[float]] = {}
_unlock_attempts_lock = threading.Lock()

app.arduino_bridge = None


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def kiosk_unlocked():
    return session.get("kiosk_unlocked") is True


def require_kiosk_unlock(f):
    @wraps(f)
    def _wrapped(*args, **kwargs):
        if not kiosk_unlocked():
            return jsonify({"error": "Kiosk locked. Enter unlock PIN."}), 403
        return f(*args, **kwargs)
    return _wrapped


def _new_pending_topup(student: dict, payment_method: str) -> dict:
    token = secrets.token_urlsafe(24)
    now = time.time()
    pending = {
        "token": token,
        "student_id": str(student.get("student_id", "")).strip(),
        "money_card": normalize_card_uid(student.get("money_card", "")),
        "payment_method": payment_method,
        "created_at": now,
        "expires_at": now + _PENDING_TOPUP_TTL,
        "amount": None,
        "result": None,
    }
    with _pending_topups_lock:
        for key, value in list(_completed_topups.items()):
            if value["expires_at"] <= now:
                _completed_topups.pop(key, None)
        for key, value in list(_pending_topups.items()):
            if value["expires_at"] <= now:
                _pending_topups.pop(key, None)
        _pending_topups[token] = pending
    return pending


def _get_pending_topup(token: str) -> dict | None:
    with _pending_topups_lock:
        pending = _pending_topups.get(token)
        if not pending or pending["expires_at"] <= time.time():
            _pending_topups.pop(token, None)
            return None
        return pending


def _allowed_amounts() -> set[float]:
    raw = os.getenv("KIOSK_DENOMINATIONS", "20,50,100,200,500,1000")
    try:
        values = {float(item.strip()) for item in raw.split(",") if item.strip()}
    except (TypeError, ValueError):
        return {20.0, 50.0, 100.0, 200.0, 500.0, 1000.0}
    return {value for value in values if isfinite(value) and value > 0}


def _decode_student_jwt(token: str) -> dict | None:
    """Decode a student app JWT (same secret as the rest of the system)."""
    try:
        return _pyjwt.decode(token, _jwt_secret, algorithms=["HS256"])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# RFID hardware
# ---------------------------------------------------------------------------

def connect_arduino(port: str, baud: int = 9600):
    """Open the RFID reader (and bill-validator channel) over serial."""
    if not _HARDWARE_OK:
        return False, "Hardware (pyserial/arduino_bridge) not available"
    try:
        import serial
    except Exception as e:
        return False, f"pyserial unavailable: {e}"
    try:
        ser = serial.Serial(port, baud, timeout=1)
        app.card_reader_state = ser
        bridge = ArduinoBridge(ser, socketio)
        app.arduino_bridge = bridge
        bridge.start_background_listener()
        logger.info("event=kiosk_arduino_connected port=%s", port)
        return True, "connected"
    except Exception as e:
        logger.error("event=kiosk_arduino_connect_failed error=%s", e)
        return False, str(e)


# ---------------------------------------------------------------------------
# Top-up flow
# ---------------------------------------------------------------------------

@app.route("/api/kiosk/health", methods=["GET"])
def health():
    db_ok = False
    try:
        db_ok = _get_kiosk_db().test_connection()
    except Exception:
        db_ok = False
    return jsonify({
        "service": "loading-kiosk",
        "status": "ok",
        "db": db_ok,
        "hardware": _HARDWARE_OK,
        "rfid_connected": bool(getattr(app, "arduino_bridge", None)),
    })


@app.route("/api/kiosk/unlock", methods=["POST"])
def unlock():
    """Operator unlocks settings with the kiosk PIN."""
    data = request.get_json(silent=True) or {}
    pin = str(data.get("pin", "")).strip()
    now = time.time()
    source = request.remote_addr or "unknown"
    with _unlock_attempts_lock:
        attempts = [stamp for stamp in _unlock_attempts.get(source, []) if now - stamp < 60]
        if len(attempts) >= 5:
            return jsonify({"success": False, "error": "Too many attempts. Try again later."}), 429
        attempts.append(now)
        _unlock_attempts[source] = attempts
    if pin == KIOSK_UNLOCK_PIN:
        with _unlock_attempts_lock:
            _unlock_attempts.pop(source, None)
        session["kiosk_unlocked"] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid PIN"}), 401


@app.route("/api/kiosk/serial/connect", methods=["POST"])
def serial_connect():
    """Operator connects the RFID reader (admin-only style action -> unlock)."""
    if not kiosk_unlocked():
        return jsonify({"error": "Kiosk locked. Enter unlock PIN."}), 403
    data = request.get_json(silent=True) or {}
    port = data.get("port") or os.getenv("SERIAL_PORT", "COM3")
    ok, msg = connect_arduino(port, int(data.get("baud_rate", 9600)))
    return jsonify({"success": ok, "message": msg}), (200 if ok else 400)


@app.route("/api/kiosk/topup/card-scan", methods=["POST"])
@require_kiosk_unlock
def topup_card_scan():
    """Identify the student by a tapped money-card UID (from RFID reader)."""
    data = request.get_json(silent=True) or {}
    uid = normalize_card_uid(str(data.get("uid", "")).strip())
    if not uid or not UID_PATTERN.match(uid):
        return jsonify({"success": False, "error": "Invalid card UID"}), 400
    try:
        res = get_student_balance(money_card=uid)
    except (APIError, SpreadsheetNotFound, WorksheetNotFound, ConnectionError, TimeoutError):
        return jsonify({"error": "Service unavailable"}), 503
    except Exception as e:
        logger.error("event=kiosk_card_lookup_error error=%s", exc_info=True)
        return jsonify({"error": "Lookup failed"}), 500
    if not res.get("success"):
        return jsonify({"success": False, "error": res.get("error", "Not found")}), res.get("status", 404)
    pending = _new_pending_topup(res, "cash")
    return jsonify({"success": True, "student": res, "pending_id": pending["token"]})


@app.route("/api/kiosk/topup/qr-scan", methods=["POST"])
@require_kiosk_unlock
def topup_qr_scan():
    """Cardless top-up: decode the student's app QR (a signed JWT)."""
    data = request.get_json(silent=True) or {}
    token = str(data.get("qr_data", "")).strip()
    if not token:
        return jsonify({"success": False, "error": "Missing QR data"}), 400

    # The QR may be a raw JWT, or a topup-session token minted by the API.
    payload = _decode_student_jwt(token)
    if payload and str(payload.get("role", "")) in ("student", "parent"):
        student_id = str(payload.get("user_id", "")).strip()
    else:
        # Fall back to a server-minted one-time topup session token.
        sess = topup_sessions.resolve(token)
        if not sess:
            return jsonify({"success": False, "error": "Invalid or expired QR"}), 400
        student_id = str(sess.get("student_id", "")).strip()

    if not student_id:
        return jsonify({"success": False, "error": "QR has no student identity"}), 400

    try:
        res = get_student_balance(student_id=student_id)
    except (APIError, SpreadsheetNotFound, WorksheetNotFound, ConnectionError, TimeoutError):
        return jsonify({"error": "Service unavailable"}), 503
    except Exception:
        return jsonify({"error": "Lookup failed"}), 500
    if not res.get("success"):
        return jsonify({"success": False, "error": res.get("error", "Not found")}), res.get("status", 404)
    pending = _new_pending_topup(res, "cardless_qr")
    return jsonify({"success": True, "student": res, "cardless": True, "pending_id": pending["token"]})


@app.route("/api/kiosk/topup/student-lookup", methods=["POST"])
@require_kiosk_unlock
def topup_student_lookup():
    """Staff-assisted: look up by Student ID (no card / no phone needed)."""
    data = request.get_json(silent=True) or {}
    student_id = str(data.get("student_id", "")).strip()
    if not student_id:
        return jsonify({"success": False, "error": "student_id required"}), 400
    try:
        res = get_student_balance(student_id=student_id)
    except (APIError, SpreadsheetNotFound, WorksheetNotFound, ConnectionError, TimeoutError):
        return jsonify({"error": "Service unavailable"}), 503
    except Exception:
        return jsonify({"error": "Lookup failed"}), 500
    if not res.get("success"):
        return jsonify({"success": False, "error": res.get("error", "Not found")}), res.get("status", 404)
    pending = _new_pending_topup(res, "cash")
    return jsonify({"success": True, "student": res, "pending_id": pending["token"]})


@app.route("/api/kiosk/topup/cash-accept", methods=["POST"])
@require_kiosk_unlock
def topup_cash_accept():
    """Record accepted cash before the balance mutation."""
    data = request.get_json(silent=True) or {}
    pending = _get_pending_topup(str(data.get("pending_id", "")).strip())
    if not pending:
        return jsonify({"success": False, "error": "Invalid or expired pending top-up"}), 400
    try:
        amount = float(data.get("amount"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid amount"}), 400
    if not isfinite(amount) or amount <= 0 or amount not in _allowed_amounts():
        return jsonify({"success": False, "error": "Amount is not an allowed denomination"}), 400
    with _pending_topups_lock:
        pending["amount"] = amount
    return jsonify({"success": True, "pending_id": pending["token"], "amount": amount})


@app.route("/api/kiosk/topup/confirm", methods=["POST"])
@require_kiosk_unlock
def topup_confirm():
    """Final step: credit the student's card. Amount comes from cash collected.

    Body: { student_id, amount, payment_method, reference? }
      payment_method: 'cash' (bill validator / denomination buttons) or
                      'cardless_qr' (student scanned app QR).
    """
    data = request.get_json(silent=True) or {}
    pending_id = str(data.get("pending_id", "")).strip()
    with _pending_topups_lock:
        completed = _completed_topups.get(pending_id)
    if completed:
        return jsonify({"success": True, **completed["result"]})
    pending = _get_pending_topup(pending_id)
    if not pending:
        return jsonify({"success": False, "error": "Invalid or expired pending top-up"}), 400
    if pending.get("amount") is None:
        return jsonify({"success": False, "error": "Cash has not been accepted"}), 400
    student_id = pending["student_id"]
    amount = pending["amount"]
    payment_method = pending["payment_method"]

    try:
        result = load_money(
            student_id,
            amount,
            payment_method=payment_method,
            processed_by="kiosk",
            station_id=STATION_KIOSK,
            idempotency_key=pending["token"],
        )
    except (APIError, SpreadsheetNotFound, WorksheetNotFound, ConnectionError, TimeoutError):
        return jsonify({"error": "Service unavailable, please retry"}), 503
    except Exception as e:
        logger.error("event=kiosk_topup_error error=%s", exc_info=True)
        return jsonify({"error": "Top-up failed"}), 500

    if not result.get("success"):
        return jsonify({"success": False, "error": result.get("error")}), result.get("status", 400)

    socketio.emit("topup_complete", {
        "student_id": student_id,
        "new_balance": result["new_balance"],
        "amount": amount,
    })
    with _pending_topups_lock:
        _pending_topups.pop(pending_id, None)
        _completed_topups[pending_id] = {"result": dict(result), "expires_at": time.time() + _PENDING_TOPUP_TTL}
    return jsonify({"success": True, **result})


@app.route("/api/kiosk/denominations", methods=["GET"])
@require_kiosk_unlock
def denominations():
    """Preset cash denominations offered on the touch screen."""
    try:
        raw = os.getenv("KIOSK_DENOMINATIONS", "20,50,100,200,500,1000")
        vals = [float(x) for x in raw.split(",") if x.strip()]
    except Exception:
        vals = [20.0, 50.0, 100.0, 200.0, 500.0, 1000.0]
    return jsonify({"denominations": vals})


@app.route("/", methods=["GET"])
def index():
    from flask import send_from_directory
    return send_from_directory(os.path.join(os.path.dirname(__file__), "static"), "index.html")


# Optional serial ingestion of bill-validator pulses (Arduino -> `BILL|<amount>`).
@app.route("/api/kiosk/hardware/bill", methods=["POST"])
@require_kiosk_unlock
def hardware_bill():
    """Operator/hardware posts a bill-validator pulse: { amount }.

    In a real kiosk the Arduino firmware reads the validator and sends this;
    here it is the documented ingestion point so the firmware team can wire it.
    """
    data = request.get_json(silent=True) or {}
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid amount"}), 400
    if not isfinite(amount) or amount <= 0 or amount not in _allowed_amounts():
        return jsonify({"success": False, "error": "Amount is not an allowed denomination"}), 400
    socketio.emit("bill_inserted", {"amount": amount})
    return jsonify({"success": True, "amount": amount})


if __name__ == "__main__":
    port = int(os.getenv("KIOSK_PORT", "5002"))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
