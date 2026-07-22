"""Standalone cashier runtime (port 5010).

This app runs the cashier blueprint without the admin dashboard UI so cashiers
can open a dedicated website directly.
"""

from __future__ import annotations

import json
import logging
import os
import re
import socket
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import gspread
import jwt
import pytz
import requests as _http
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, redirect, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO
from google.oauth2.service_account import Credentials

# Ensure imports work both as a package and as: python backend/cashier_app/app.py
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
for p in (str(BACKEND_DIR), str(PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

logger = logging.getLogger(__name__)

# Load .env before reading env vars
load_dotenv()

USE_SUPABASE = bool(os.getenv("DATABASE_URL"))
try:
    from sheets_adapter import get_sheets_client as _adapter_get_client
    _ADAPTER_AVAILABLE = True
except Exception as _adapter_err:
    _ADAPTER_AVAILABLE = False
    logger.warning("event=adapter_import_failed error=%s", _adapter_err)

try:
    from .cashier_routes import (  # type: ignore
        cashier_bp, _build_transaction_row, manage_inventory, update_inventory,
        cashier_history, cashier_students,
    )
except ImportError:
    from cashier_routes import (  # type: ignore
        cashier_bp, _build_transaction_row, manage_inventory, update_inventory,
        cashier_history, cashier_students,
    )


PH_TZ = pytz.timezone("Asia/Manila")
UID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}$|^[0-9A-Fa-f]{14}$")

logger = logging.getLogger(__name__)


def get_philippines_time() -> datetime:
    return datetime.now(PH_TZ)


def normalize_card_uid(uid):
    if uid is None:
        return ""
    uid_str = str(uid).strip()
    if not uid_str:
        return ""
    return uid_str.upper()


def _get_google_sheets_client():
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_FILE", "").strip()
    if not credentials_path:
        credentials_path = str(PROJECT_ROOT / "config" / "credentials.json")
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    if not os.path.exists(credentials_path) or not spreadsheet_id:
        raise RuntimeError("Google fallback requires GOOGLE_CREDENTIALS_FILE and GOOGLE_SHEETS_ID")
    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
    )
    return gspread.authorize(credentials).open_by_key(spreadsheet_id)


def get_sheets_client():
    """Use Supabase first; fall back to Google Sheets only when it is down."""
    if _ADAPTER_AVAILABLE and os.getenv("DATABASE_URL"):
        try:
            client = _adapter_get_client()
            probe = getattr(client, "test_connection", None)
            if probe is None or probe():
                return client
            logger.warning("event=supabase_unavailable fallback=google_sheets")
        except Exception as exc:
            logger.warning("event=supabase_unavailable fallback=google_sheets error=%s", exc)
    return _get_google_sheets_client()


def _decode_student_jwt(raw_token: str, jwt_secret: str):
    try:
        return jwt.decode(raw_token, jwt_secret, algorithms=["HS256"])
    except Exception:
        return None


def _build_cors_origins() -> list[str]:
    origins_str = os.getenv("CORS_ORIGINS", "")
    explicit_origins = [o.strip() for o in origins_str.split(",") if o.strip()]
    if explicit_origins:
        return explicit_origins

    port = os.getenv("CASHIER_PORT", "5010").strip() or "5010"
    origins: set[str] = {
        "http://localhost",
        f"http://localhost:{port}",
        "http://127.0.0.1",
        f"http://127.0.0.1:{port}",
        f"http://0.0.0.0:{port}",
    }

    # Auto-allow local LAN IPs for cashier access from phones/tablets on the same network.
    try:
        addrs = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        for addr in addrs:
            ip = addr[4][0]
            if ip and not ip.startswith("127."):
                origins.add(f"http://{ip}:{port}")
    except Exception:
        pass

    # Fallback probe for active outbound interface IP.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                origins.add(f"http://{ip}:{port}")
    except Exception:
        pass

    return sorted(origins)


def create_app() -> tuple[Flask, SocketIO]:
    flask_secret = os.getenv("FLASK_SECRET_KEY", "").strip()
    jwt_secret = os.getenv("JWT_SECRET", "").strip()

    if not flask_secret or "change-in-production" in flask_secret.lower():
        raise RuntimeError("FLASK_SECRET_KEY must be set and must not use insecure default")
    if not jwt_secret or (jwt_secret.lower().startswith("bangko-") and "secret-" in jwt_secret.lower()):
        raise RuntimeError("JWT_SECRET must be set and must not use insecure default")

    # Bind template/static folders to the launch directory, not Flask's import
    # root_path. When frozen by PyInstaller, root_path points into the extracted
    # _MEIPASS bundle (no templates there); in dev it equals this directory anyway,
    # so this is a no-op for the source run and correct for the .exe.
    if getattr(sys, "frozen", False):
        _launch_dir = Path(sys.executable).resolve().parent
    else:
        _launch_dir = APP_DIR
    app = Flask(
        __name__,
        template_folder=str(_launch_dir / "templates"),
        static_folder=str(_launch_dir / "static") if (_launch_dir / "static").is_dir() else None,
    )
    app.secret_key = flask_secret
    app.config["ARDUINO_WIFI_OFFLINE_S"] = int(os.getenv("ARDUINO_WIFI_OFFLINE_S", "60"))

    origins = _build_cors_origins()
    CORS(app, origins=origins)
    socketio = SocketIO(app, cors_allowed_origins=origins)

    # Shared runtime state used by cashier blueprint routes.
    app.socketio = socketio
    app.arduino_last_heartbeat = 0.0
    app.pending_qr_token = None
    app.last_qr_payment = None
    app.pending_card_read = None

    app.register_blueprint(cashier_bp)

    def _decode_cashier_cookie():
        token = request.cookies.get("jwt_token", "")
        if not token:
            return None
        try:
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        except Exception:
            return None
        if payload.get("role") not in {"cashier", "admin"}:
            return None
        return payload

    @app.before_request
    def _canonicalize_legacy_cashier_urls():
        # Keep legacy paths working, but canonicalize visible cashier URLs to native root/login.
        if request.method == "GET":
            if request.path in {"/cashier", "/cashier/"}:
                return redirect("/", code=302)
            if request.path == "/cashier/login":
                return redirect("/login", code=302)
        return None

    @app.route("/")
    def root():
        payload = _decode_cashier_cookie()
        if not payload:
            return redirect("/login")
        return render_template("cashier_index_standalone.html", user=payload)

    @app.route("/login", methods=["GET"])
    def native_login():
        payload = _decode_cashier_cookie()
        if payload:
            return redirect("/")
        return render_template("cashier_login_standalone.html")

    @app.route("/healthz")
    def healthz():
        return jsonify({"ok": True, "service": "cashier_app"})

    @app.route("/favicon.ico")
    def favicon():
        return Response(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
            '<rect width="64" height="64" rx="14" fill="#3525cd"/>'
            '<text x="32" y="45" text-anchor="middle" font-family="Georgia,serif" '
            'font-size="42" font-style="italic" fill="white">B</text></svg>',
            mimetype="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    # Native aliases (no /cashier prefix) for standalone cashier UX.
    @app.route("/api/login", methods=["POST"])
    def native_api_login():
        return app.view_functions["cashier.api_login"]()

    @app.route("/api/logout", methods=["POST"])
    def native_api_logout():
        return app.view_functions["cashier.api_logout"]()

    @app.route("/api/products", methods=["GET"])
    def native_api_products():
        return app.view_functions["cashier.get_products"]()

    @app.route("/api/inventory", methods=["GET", "POST"])
    def native_api_inventory():
        return app.view_functions["cashier.manage_inventory"]()

    @app.route("/api/inventory/<product_id>", methods=["PUT", "DELETE"])
    def native_api_inventory_product(product_id):
        return app.view_functions["cashier.update_inventory"](product_id)

    @app.route("/api/history", methods=["GET"])
    def native_api_history():
        return app.view_functions["cashier.cashier_history"]()

    @app.route("/api/students", methods=["GET"])
    def native_api_students():
        return app.view_functions["cashier.cashier_students"]()

    @app.route("/api/process-sale", methods=["POST"])
    def native_api_process_sale():
        return app.view_functions["cashier.process_sale"]()

    @app.route("/api/complete-sale", methods=["POST"])
    def native_api_complete_sale():
        return app.view_functions["cashier.complete_sale"]()

    @app.route("/api/complete-sale-nfc", methods=["POST"])
    def native_api_complete_sale_nfc():
        return app.view_functions["cashier.complete_sale_nfc"]()

    @app.route("/api/cancel-sale", methods=["POST"])
    def native_api_cancel_sale():
        return app.view_functions["cashier.cancel_sale"]()

    @app.route("/api/ports", methods=["GET"])
    def native_api_ports():
        return app.view_functions["cashier.get_ports"]()

    @app.route("/api/connect-arduino", methods=["POST"])
    def native_api_connect_arduino():
        return app.view_functions["cashier.connect_arduino"]()

    @app.route("/api/queue/status", methods=["GET"])
    def native_api_queue_status():
        return app.view_functions["cashier.queue_status"]()

    @app.route("/api/queue/sync", methods=["POST"])
    def native_api_queue_sync():
        return app.view_functions["cashier.queue_sync"]()

    @app.route("/api/arduino-wifi-status", methods=["GET"])
    def native_api_arduino_wifi_status():
        return app.view_functions["cashier.arduino_wifi_status"]()

    @app.route("/api/qr-generate", methods=["POST"])
    def native_api_qr_generate():
        return app.view_functions["cashier.qr_generate"]()

    @app.route("/api/arduino/heartbeat", methods=["POST"])
    def arduino_heartbeat():
        api_key = request.headers.get("X-API-Key", "")
        required_key = os.getenv("ARDUINO_API_KEY", "")
        if not required_key or api_key != required_key:
            return jsonify({"error": "Unauthorized"}), 401

        app.arduino_last_heartbeat = time.time()
        socketio.emit("arduino_wifi_status", {"online": True, "last_seen_s": 0.0})
        return jsonify({"status": "ok"}), 200

    @app.route("/api/arduino/card-read", methods=["POST"])
    def arduino_card_read():
        api_key = request.headers.get("X-API-Key", "")
        required_key = os.getenv("ARDUINO_API_KEY", "")
        if not required_key or api_key != required_key:
            return jsonify({"error": "Unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        uid = str(data.get("uid", "")).strip()
        if not UID_PATTERN.match(uid):
            return jsonify({"error": "Invalid UID format"}), 400

        app.pending_card_read = {"uid": uid, "created_at": time.time()}
        logger.info("event=arduino_card_read_received uid=%s", uid)
        socketio.emit("card_read", {"success": True, "uid": uid})
        return jsonify({"status": "ok"}), 200

    @app.route("/api/arduino/card-read-pending", methods=["GET"])
    def arduino_card_read_pending():
        payload = _decode_cashier_cookie()
        if not payload:
            return jsonify({"error": "Unauthorized"}), 401

        pending = app.pending_card_read
        if pending is None:
            return jsonify({"uid": None}), 200

        if time.time() - pending.get("created_at", 0) > 10:
            app.pending_card_read = None
            return jsonify({"uid": None}), 200

        uid = pending.get("uid")
        app.pending_card_read = None  # one-shot consume to avoid duplicate complete-sale calls
        logger.info("event=arduino_card_read_consumed uid=%s", uid)
        return jsonify({"uid": uid}), 200

    @app.route("/api/arduino/qr-pending", methods=["GET"])
    def arduino_qr_pending():
        api_key = request.headers.get("X-API-Key", "")
        required_key = os.getenv("ARDUINO_API_KEY", "")
        if not required_key or api_key != required_key:
            return jsonify({"error": "Unauthorized"}), 401

        pending = app.pending_qr_token
        if pending is None or time.time() - pending.get("created_at", 0) > 300:
            return jsonify({"token": None})

        return jsonify(
            {
                "token": pending.get("token"),
                "url": pending.get("url"),
                "qr_value": pending.get("qr_value", pending.get("token")),
            }
        )

    @app.route("/api/qr/<token>", methods=["GET"])
    def qr_cart(token: str):
        auth_header = request.headers.get("Authorization", "")
        bearer = auth_header.replace("Bearer ", "").strip()
        payload = _decode_student_jwt(bearer, jwt_secret)
        if not payload:
            return jsonify({"error": "Unauthorized"}), 401

        pending = app.pending_qr_token
        if pending is None:
            return jsonify({"error": "QR expired or not found"}), 404
        if pending.get("token") != token:
            return jsonify({"error": "QR expired or not found"}), 404
        if time.time() - pending.get("created_at", 0) > 300:
            app.pending_qr_token = None
            return jsonify({"error": "QR token expired"}), 410

        return jsonify(
            {
                "items": pending.get("cart_snapshot", []),
                "total": pending.get("total", 0.0),
                "cashier": pending.get("cashier_username", ""),
            }
        )

    @app.route("/api/qr/confirm", methods=["POST"])
    def qr_confirm():
        auth_header = request.headers.get("Authorization", "")
        bearer = auth_header.replace("Bearer ", "").strip()
        payload = _decode_student_jwt(bearer, jwt_secret)
        if not payload:
            return jsonify({"error": "Unauthorized"}), 401

        body = request.get_json(silent=True) or {}
        token_param = str(body.get("token", "")).strip()
        pending = app.pending_qr_token

        if pending is None or pending.get("token") != token_param:
            return jsonify({"error": "QR expired or not found"}), 404
        if time.time() - pending.get("created_at", 0) > 300:
            app.pending_qr_token = None
            return jsonify({"error": "QR token expired"}), 410

        student_id = str(payload.get("user_id", "")).strip()
        items = pending.get("cart_snapshot", [])
        total = float(pending.get("total", 0))

        try:
            db = get_sheets_client()

            users_sheet = db.worksheet("Users")
            user_records = users_sheet.get_all_records()
            matched_user = None
            money_card_number = ""
            for user in user_records:
                if str(user.get("StudentID", "")).strip() == student_id:
                    matched_user = user
                    money_card_number = normalize_card_uid(user.get("MoneyCardNumber", ""))
                    break

            if not money_card_number:
                return jsonify({"error": "Student not found"}), 404

            money_sheet = db.worksheet("Money Accounts")
            money_records = money_sheet.get_all_records()

            account_row = None
            current_balance = 0.0
            card_status = ""
            for idx, record in enumerate(money_records, start=2):
                rec_uid = normalize_card_uid(record.get("MoneyCardNumber", ""))
                if rec_uid == money_card_number:
                    account_row = idx
                    current_balance = float(record.get("Balance", 0) or 0)
                    card_status = str(record.get("Status", "")).strip().lower()
                    break

            if account_row is None:
                return jsonify({"error": "Money account not found"}), 404
            if card_status == "lost":
                return jsonify({"error": "Card reported as lost"}), 403
            if card_status and card_status != "active":
                return jsonify({"error": f"Card is {card_status}"}), 403
            if current_balance < total:
                return jsonify(
                    {
                        "error": "Insufficient funds",
                        "balance": current_balance,
                        "required": total,
                    }
                ), 402

            new_balance = current_balance - total
            timestamp_dt = get_philippines_time()
            timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")
            transaction_id = f"TXN-{timestamp_dt.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"

            trans_sheet = db.worksheet("Transactions Log")
            transaction_row = _build_transaction_row(
                trans_sheet,
                transaction_id=transaction_id,
                timestamp=timestamp,
                student_id=student_id,
                money_card_number=money_card_number,
                transaction_type="QR Purchase",
                amount=total,
                balance_before=current_balance,
                balance_after=new_balance,
                status="Completed",
                error_message="",
                items=items,
                station_id="cashier-standalone-qr",
            )

            money_sheet.update_cell(account_row, 3, new_balance)
            try:
                trans_sheet.append_row(transaction_row)
            except Exception as log_err:
                try:
                    money_sheet.update_cell(account_row, 3, current_balance)
                    logger.error(
                        "qr_confirm: rolled back balance to %s for student %s after transaction log failure. Error: %s",
                        current_balance,
                        student_id,
                        log_err,
                    )
                except Exception as rollback_err:
                    logger.error(
                        "qr_confirm: CRITICAL rollback failed for student %s. Rollback error: %s. Original error: %s",
                        student_id,
                        rollback_err,
                        log_err,
                    )
                return jsonify({"error": "Service unavailable, please try again"}), 503

            # Emit before clearing pending token to avoid race (see KNOWLEDGE.md)
            socketio.emit(
                "qr_payment",
                {
                    "success": True,
                    "new_balance": new_balance,
                    "timestamp": timestamp,
                    "total": total,
                    "cashier": pending.get("cashier_username", ""),
                },
            )

            app.last_qr_payment = {
                "token": token_param,
                "new_balance": new_balance,
                "timestamp": timestamp,
                "total": total,
            }
            app.pending_qr_token = None

            return jsonify(
                {
                    "success": True,
                    "new_balance": new_balance,
                    "timestamp": timestamp,
                }
            )

        except (gspread.exceptions.APIError, ConnectionError, TimeoutError):
            return jsonify({"error": "Service unavailable, please try again"}), 503
        except Exception:
            return jsonify({"error": "An unexpected error occurred"}), 500

    @app.route("/api/cashier/qr-paid", methods=["POST"])
    def cashier_qr_paid_callback():
        """Cloud callback endpoint used by QR sync mode (authenticated)."""
        shared_secret = (os.getenv("CASHIER_SHARED_SECRET", "").strip()
                         or os.getenv("JWT_SECRET", "").strip())
        header_secret = request.headers.get("X-Cashier-Secret", "")
        if not shared_secret or header_secret != shared_secret:
            return jsonify({"error": "Unauthorized"}), 401

        payload = request.get_json(silent=True) or {}
        token = str(payload.get("token", "")).strip()
        pending = app.pending_qr_token or {}
        if token and pending.get("token") and token != pending.get("token"):
            return jsonify({"status": "ignored", "reason": "token_mismatch"}), 200

        app.last_qr_payment = {
            "token": token,
            "new_balance": payload.get("new_balance"),
            "timestamp": payload.get("timestamp"),
            "total": payload.get("total"),
        }
        socketio.emit(
            "qr_payment",
            {
                "success": True,
                "new_balance": payload.get("new_balance"),
                "timestamp": payload.get("timestamp"),
                "total": payload.get("total"),
            },
        )
        app.pending_qr_token = None
        return jsonify({"status": "ok"}), 200

    @app.route("/api/qr-paid", methods=["POST"])
    def qr_paid_status():
        """Cashier UI poll endpoint (no shared-secret header required).

        Primary source: local callback-populated state.
        Fallback: poll cloud /api/cashier/qr-status so cashier UI can still resolve
        when callback delivery is delayed/unavailable.
        """
        payload = request.get_json(silent=True) or {}
        token = str(payload.get("token", "")).strip()

        result = app.last_qr_payment
        if result and (not token or result.get("token") == token):
            app.last_qr_payment = None
            return jsonify({"paid": True, **result}), 200

        # Cloud polling fallback for split local-cashier / cloud-QR deployments.
        pa_url = os.getenv("PYTHONANYWHERE_URL", "").rstrip("/")
        shared_secret = (os.getenv("CASHIER_SHARED_SECRET", "").strip()
                         or os.getenv("JWT_SECRET", "").strip())
        if token and pa_url and shared_secret:
            try:
                resp = _http.get(
                    f"{pa_url}/api/cashier/qr-status",
                    params={"token": token},
                    headers={"X-Cashier-Secret": shared_secret},
                    timeout=5,
                )
                if resp.status_code == 200:
                    remote = resp.json() or {}
                    if remote.get("paid"):
                        result = {
                            "token": token,
                            "new_balance": remote.get("new_balance"),
                            "timestamp": remote.get("timestamp"),
                            "total": remote.get("total"),
                        }
                        socketio.emit(
                            "qr_payment",
                            {
                                "success": True,
                                "new_balance": result.get("new_balance"),
                                "timestamp": result.get("timestamp"),
                                "total": result.get("total"),
                            },
                        )
                        pending = app.pending_qr_token or {}
                        if not pending.get("token") or pending.get("token") == token:
                            app.pending_qr_token = None
                        return jsonify({"paid": True, **result}), 200
            except Exception:
                pass

        return jsonify({"paid": False}), 200

    return app, socketio


app, socketio = create_app()


if __name__ == "__main__":
    port = int(os.getenv("CASHIER_PORT", "5010"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    socketio.run(app, host="127.0.0.1", port=port, debug=debug)
