"""
Arduino NFC Bridge
Handles serial communication with R3/R4 Arduino sketches using pipe-delimited protocol.
Wire formats: NFC|<token>, CARD|<uid>, ERROR|<msg>
"""

import os
import time
import threading
import requests


class ArduinoBridge:
    def __init__(self, arduino_serial, socketio):
        self.arduino = arduino_serial
        self.socketio = socketio
        self.reading_active = False
        self.current_callback = None
        self.timeout_seconds = 5
        self._serial_thread = None
        self._start_serial_thread()

    def _start_serial_thread(self):
        """Start the background serial reader thread (daemon).
        Named method so tests can patch it via patch.object."""
        self._serial_thread = threading.Thread(target=self._serial_loop, daemon=True)
        self._serial_thread.start()

    def start_background_listener(self):
        """Called by dashboard_core.py after construction.
        Restarts the thread if it died; no-op if already alive."""
        if self._serial_thread is None or not self._serial_thread.is_alive():
            self._start_serial_thread()

    def _serial_loop(self):
        """Background loop: read lines from serial port and dispatch via _parse_line."""
        while self.arduino and self.arduino.is_open:
            try:
                if self.arduino.in_waiting > 0:
                    raw = self.arduino.readline()
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line:
                        self._parse_line(line)
                time.sleep(0.05)
            except Exception:
                break  # exit loop on serial error; bridge reconnect is handled externally

    def _parse_line(self, line: str):
        """Parse one serial output line and emit appropriate SocketIO event.

        Wire formats (pipe-delimited, no angle brackets):
          NFC|<48-char-token>     → emit 'nfc_payment' + POST to /api/nfc/pay
          CARD|<uid-hex>          → emit 'card_read' + trigger reading_active callback
          ERROR|<msg>             → emit 'nfc_payment_result' with success=False
        """
        if line.startswith("NFC|"):
            token = line[4:]
            self.socketio.emit("nfc_payment", {"token": token})
            self._post_nfc_payment(token)
        elif line.startswith("CARD|"):
            uid = line[5:]
            self.socketio.emit("card_read", {"success": True, "uid": uid})
            if self.reading_active and self.current_callback:
                self.reading_active = False
                cb = self.current_callback
                self.current_callback = None
                cb(uid)
        elif line.startswith("ERROR|"):
            error = line[6:]
            self.socketio.emit("nfc_payment_result", {"success": False, "error": error})

    def _post_nfc_payment(self, token: str):
        """POST NFC token to /api/nfc/pay with CASHIER_JWT Bearer auth.
        Silently returns if CASHIER_JWT is not set (logs warning)."""
        jwt = os.environ.get("CASHIER_JWT", "")
        if not jwt:
            print("[ArduinoBridge] WARNING: CASHIER_JWT not set — skipping POST")
            return
        base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:5001")
        try:
            requests.post(
                f"{base_url}/api/nfc/pay",
                json={"token": token},
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=5,
            )
        except Exception as e:
            print(f"[ArduinoBridge] _post_nfc_payment error: {e}")

    def read_card_with_timeout(self, callback, timeout=5):
        """Set up one-shot card read. Background serial loop will call callback
        when a CARD| line is received, or emit card_timeout after `timeout` seconds."""
        if not self.arduino or not self.arduino.is_open:
            self.socketio.emit("card_error", {"message": "Arduino not connected"})
            return False
        self.reading_active = True
        self.current_callback = callback
        self.timeout_seconds = timeout
        t = threading.Thread(target=self._timeout_watcher, daemon=True)
        t.start()
        return True

    def _timeout_watcher(self):
        """Emit card_timeout if reading_active is still True after timeout_seconds."""
        time.sleep(self.timeout_seconds)
        if self.reading_active:
            self.reading_active = False
            self.current_callback = None
            self.socketio.emit(
                "card_timeout",
                {"message": f"No card detected within {self.timeout_seconds} seconds"},
            )

    def cancel_reading(self):
        """Cancel an in-progress read_card_with_timeout session."""
        self.reading_active = False
        self.current_callback = None
