"""
Arduino RC522 Bridge with Timeout Support
Handles card reading with configurable timeout for cashier transactions.
Extended with NFC payment serial parsing (NFC|<token> and ERROR|NFC_FAIL).
"""

import sys
import os
import time
import logging
import threading
import requests
from flask_socketio import emit

try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from errors import get_logger

    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

# NFC payment env vars — read once at import time; also re-read per call for testability
_CASHIER_JWT = os.environ.get("CASHIER_JWT", "")
_API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:5001")
if not _CASHIER_JWT:
    logging.warning("CASHIER_JWT env var not set — NFC payment POSTs will lack auth")

STATION_ID = os.getenv("STATION_ID", "main")
STATION_SERIAL_PORT = os.getenv("STATION_SERIAL_PORT", "")


class ArduinoBridge:
    def __init__(self, arduino_serial, socketio):
        self.arduino = arduino_serial
        self.socketio = socketio
        self.reading_active = False
        self.current_callback = None
        self.timeout_seconds = 5
        if self.arduino is None and STATION_SERIAL_PORT:
            try:
                import serial as _serial

                self.arduino = _serial.Serial(STATION_SERIAL_PORT, 9600, timeout=2)
                time.sleep(2)
                logger.info(f"Auto-connected to {STATION_SERIAL_PORT}")
            except Exception as e:
                logger.warning(f"Auto-connect failed on {STATION_SERIAL_PORT}: {e}")

    # ── NFC serial line parsing ──────────────────────────────────────

    def _parse_line(self, line: str) -> None:
        """Route a stripped serial line to the correct handler."""
        if line.startswith("NFC|"):
            token = line[4:]  # 48-char ASCII token after strip()
            self.socketio.emit("nfc_payment", {"token": token})
            # Fire POST in daemon thread so serial loop is not blocked
            t = threading.Thread(
                target=self._post_nfc_payment, args=(token,), daemon=True
            )
            t.start()
        elif line == "ERROR|NFC_FAIL":
            self.socketio.emit(
                "nfc_payment_result", {"success": False, "error": "NFC_FAIL"}
            )
        elif line.startswith("CARD|"):
            uid = line[5:]
            if len(uid) in (8, 14):  # 4-byte MIFARE (8 hex) or 7-byte (14 hex)
                self.socketio.emit("card_read", {"uid": uid})
        # Any other lines are ignored silently

    def _post_nfc_payment(self, token: str) -> None:
        """POST token to /api/nfc/pay in a daemon thread. Called from _parse_line."""
        jwt = os.environ.get("CASHIER_JWT", _CASHIER_JWT)
        api_base = os.environ.get("API_BASE_URL", _API_BASE_URL)
        url = f"{api_base}/api/nfc/pay"
        headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}
        headers["X-Station-ID"] = STATION_ID
        try:
            resp = requests.post(
                url, json={"virtual_card_token": token}, headers=headers, timeout=10
            )
            if resp.status_code != 200:
                logging.warning("NFC pay POST returned %s", resp.status_code)
                self.socketio.emit(
                    "nfc_payment_result",
                    {"success": False, "error": f"HTTP {resp.status_code}"},
                )
            # Success result is emitted by the API endpoint via its own SocketIO emit (not here)
        except Exception as exc:
            logging.error("NFC pay POST failed: %s", exc)
            self.socketio.emit(
                "nfc_payment_result", {"success": False, "error": str(exc)}
            )

    def _start_serial_thread(self) -> None:
        """Start the serial reader daemon thread. Extracted for testability."""
        t = threading.Thread(target=self._read_card_thread, daemon=True)
        t.start()

    def start_background_listener(self) -> None:
        """Start a persistent background daemon that routes every serial line
        through _parse_line() until the serial port is closed or gone.

        Unlike _read_card_thread(), this loop has NO timeout — it runs
        indefinitely.  NFC|, ERROR|NFC_FAIL, and CARD| lines are all handled.
        Call this once after the serial connection is established (e.g. from
        connect_serial in dashboard_core.py).
        """
        t = threading.Thread(target=self._background_listener_loop, daemon=True)
        t.daemon = True
        t.start()
        logger.info("event=background_listener_started")

    def _background_listener_loop(self) -> None:
        """Daemon thread body for the persistent serial listener."""
        logger.info("event=background_listener_loop_running")
        while True:
            try:
                ard = self.arduino
                if ard is None or not ard.is_open:
                    # Port closed — exit the loop
                    logger.info(
                        "event=background_listener_loop_exit reason=port_closed"
                    )
                    return
                if ard.in_waiting > 0:
                    line = ard.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        self._parse_line(line)
                else:
                    time.sleep(0.05)
            except Exception as exc:
                # Port gone / OS error — stop listening
                logger.warning(
                    "event=background_listener_loop_exit reason=exception error=%s", exc
                )
                return

    # ── Existing card-read API ───────────────────────────────────────

    def read_card_with_timeout(self, callback, timeout=5):
        """
        Read card with timeout
        callback: function(card_uid) called on success
        timeout: seconds to wait before timeout
        """
        if not self.arduino or not self.arduino.is_open:
            self.socketio.emit("card_error", {"message": "Arduino not connected"})
            return False

        self.reading_active = True
        self.current_callback = callback
        self.timeout_seconds = timeout

        thread = threading.Thread(target=self._read_card_thread)
        thread.daemon = True
        thread.start()

        return True

    def _read_card_thread(self):
        """Background thread to read card with timeout"""
        if not self.arduino or not self.arduino.is_open:
            self.socketio.emit("card_error", {"message": "Arduino not connected"})
            self.reading_active = False
            return

        try:
            self.arduino.reset_input_buffer()
            start_time = time.time()

            while (
                self.reading_active
                and (time.time() - start_time) < self.timeout_seconds
            ):
                try:
                    if self.arduino.in_waiting > 0:
                        line = (
                            self.arduino.readline()
                            .decode("utf-8", errors="ignore")
                            .strip()
                        )

                        # Route NFC lines through _parse_line (handles NFC|, ERROR|NFC_FAIL)
                        if line.startswith("NFC|") or line.startswith("ERROR|"):
                            self._parse_line(line)
                        # Expected format: CARD|ABCD1234 (no angle brackets — firmware format)
                        elif line.startswith("CARD|"):
                            uid = line[5:]
                            if len(uid) in (8, 14):
                                self.reading_active = False

                                # Call the callback with card UID
                                if self.current_callback:
                                    self.current_callback(uid)

                                # Emit success event (include uid for cashier_index.html compatibility)
                                self.socketio.emit(
                                    "card_read", {"success": True, "uid": uid}
                                )
                                return

                    time.sleep(0.1)

                except Exception as e:
                    logger.error("event=card_read_error error=%s", e)
                    time.sleep(0.1)

            # Timeout reached
            self.reading_active = False
            self.socketio.emit(
                "card_timeout",
                {"message": f"No card detected within {self.timeout_seconds} seconds"},
            )

        except Exception as e:
            logger.error("event=card_read_thread_error error=%s", e)
            self.socketio.emit("card_error", {"message": str(e)})
            self.reading_active = False

    def cancel_reading(self):
        """Cancel active card reading"""
        self.reading_active = False
        self.current_callback = None
