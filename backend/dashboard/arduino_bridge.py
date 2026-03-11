"""
Arduino NFC Bridge
Handles serial communication with R3/R4 Arduino sketches using pipe-delimited protocol.
Wire formats: NFC|<token>, CARD|<uid>, ERROR|<msg>

Offline Grace Queue
-------------------
NFC payments that fail (server unreachable, timeout, 5xx) are queued in memory
and retried automatically every RETRY_INTERVAL_SECONDS on a background thread.
The queue holds up to MAX_QUEUE_SIZE items; oldest entries are dropped if full.
This keeps the canteen running during brief network blips without losing payments.
"""

import logging
import os
import queue
import threading
import time

import requests

logger = logging.getLogger("bangko.arduino_bridge")

# ── Offline queue configuration ──────────────────────────────────────────────
MAX_QUEUE_SIZE = 50          # max queued NFC payments (oldest dropped when full)
RETRY_INTERVAL_SECONDS = 15  # how often the retry worker wakes up
MAX_RETRIES = 10             # drop a queued payment after this many failed attempts
REQUEST_TIMEOUT_SECONDS = 5  # per-attempt POST timeout


class _QueuedPayment:
    """One NFC payment waiting to be delivered."""

    __slots__ = ("token", "attempt", "queued_at")

    def __init__(self, token: str):
        self.token: str = token
        self.attempt: int = 0
        self.queued_at: float = time.monotonic()


class ArduinoBridge:
    def __init__(self, arduino_serial, socketio):
        self.arduino = arduino_serial
        self.socketio = socketio
        self.reading_active = False
        self.current_callback = None
        self.timeout_seconds = 5
        self._serial_thread = None

        # Offline payment queue
        self._payment_queue: queue.Queue[_QueuedPayment] = queue.Queue(
            maxsize=MAX_QUEUE_SIZE
        )
        self._retry_thread = threading.Thread(
            target=self._retry_loop, daemon=True, name="nfc-retry"
        )
        self._retry_thread.start()

        self._start_serial_thread()

    # ── Serial thread ─────────────────────────────────────────────────────────

    def _start_serial_thread(self):
        """Start the background serial reader thread (daemon).
        Named method so tests can patch it via patch.object."""
        self._serial_thread = threading.Thread(
            target=self._serial_loop, daemon=True, name="arduino-serial"
        )
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
                break  # exit loop on serial error; bridge reconnect handled externally

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

    # ── NFC payment delivery (with offline queue) ─────────────────────────────

    def _post_nfc_payment(self, token: str, *, is_retry: bool = False):
        """POST NFC token to /api/nfc/pay.

        On network failure or 5xx response, the payment is queued for automatic
        retry so brief outages don't silently drop transactions.

        Returns True if the POST succeeded, False otherwise.
        """
        jwt = os.environ.get("CASHIER_JWT", "")
        if not jwt:
            logger.warning("CASHIER_JWT not set — skipping NFC payment POST")
            return False

        base_url = os.environ.get("API_BASE_URL", "http://127.0.0.1:5001")
        url = f"{base_url}/api/nfc/pay"

        try:
            resp = requests.post(
                url,
                json={"token": token},
                headers={"Authorization": f"Bearer {jwt}"},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            if resp.status_code < 500:
                # 2xx = success; 4xx = permanent error (bad token etc.) — don't retry
                if resp.status_code >= 400:
                    logger.warning(
                        "NFC payment rejected permanently status=%d token_prefix=%s",
                        resp.status_code,
                        token[:8],
                    )
                else:
                    logger.info(
                        "NFC payment delivered%s status=%d",
                        " (retry)" if is_retry else "",
                        resp.status_code,
                    )
                    self.socketio.emit(
                        "nfc_payment_result", {"success": True, "retried": is_retry}
                    )
                return True

            # 5xx — server error, worth retrying
            logger.warning(
                "NFC payment got 5xx status=%d — queuing for retry", resp.status_code
            )

        except requests.exceptions.ConnectionError:
            logger.warning("NFC payment failed (connection refused) — queuing for retry")
        except requests.exceptions.Timeout:
            logger.warning("NFC payment timed out — queuing for retry")
        except Exception as exc:
            logger.warning("NFC payment unexpected error: %s — queuing for retry", exc)

        if not is_retry:
            self._enqueue_payment(token)

        return False

    def _enqueue_payment(self, token: str):
        """Add a failed payment to the offline queue for later retry.

        If the queue is full, the oldest item is dropped to make room.
        """
        item = _QueuedPayment(token)
        if self._payment_queue.full():
            try:
                dropped = self._payment_queue.get_nowait()
                logger.warning(
                    "Offline queue full — dropped oldest payment token_prefix=%s",
                    dropped.token[:8],
                )
                self.socketio.emit(
                    "nfc_queue_overflow",
                    {"dropped_token_prefix": dropped.token[:8]},
                )
            except queue.Empty:
                pass

        try:
            self._payment_queue.put_nowait(item)
            depth = self._payment_queue.qsize()
            logger.info(
                "NFC payment queued for retry token_prefix=%s queue_depth=%d",
                token[:8],
                depth,
            )
            self.socketio.emit(
                "nfc_payment_queued",
                {"queue_depth": depth},
            )
        except queue.Full:
            logger.error("Could not enqueue NFC payment — queue still full after drain")

    def _retry_loop(self):
        """Background thread: drain the offline queue every RETRY_INTERVAL_SECONDS."""
        while True:
            time.sleep(RETRY_INTERVAL_SECONDS)
            self._drain_queue()

    def _drain_queue(self):
        """Try to deliver all queued payments. Items that succeed or exceed
        MAX_RETRIES are removed; others are re-queued for the next cycle."""
        if self._payment_queue.empty():
            return

        pending = []
        while not self._payment_queue.empty():
            try:
                pending.append(self._payment_queue.get_nowait())
            except queue.Empty:
                break

        if not pending:
            return

        logger.info("Retrying %d queued NFC payment(s)", len(pending))
        requeue = []

        for item in pending:
            item.attempt += 1
            if item.attempt > MAX_RETRIES:
                age = time.monotonic() - item.queued_at
                logger.error(
                    "Dropping NFC payment after %d attempts age=%.0fs token_prefix=%s",
                    item.attempt - 1,
                    age,
                    item.token[:8],
                )
                self.socketio.emit(
                    "nfc_payment_failed_permanent",
                    {
                        "token_prefix": item.token[:8],
                        "attempts": item.attempt - 1,
                    },
                )
                continue

            success = self._post_nfc_payment(item.token, is_retry=True)
            if not success:
                requeue.append(item)

        # Put back items that still need retrying
        for item in requeue:
            try:
                self._payment_queue.put_nowait(item)
            except queue.Full:
                logger.error(
                    "Re-queue failed (queue full) token_prefix=%s", item.token[:8]
                )

        remaining = self._payment_queue.qsize()
        if remaining:
            logger.info("Retry cycle complete — %d payment(s) still pending", remaining)

    # ── Queue status (for dashboard / health endpoint) ────────────────────────

    def queue_status(self) -> dict:
        """Return a snapshot of the offline queue for monitoring."""
        return {
            "queued": self._payment_queue.qsize(),
            "max_size": MAX_QUEUE_SIZE,
            "retry_interval_seconds": RETRY_INTERVAL_SECONDS,
            "max_retries": MAX_RETRIES,
        }

    # ── Card reading ──────────────────────────────────────────────────────────

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
