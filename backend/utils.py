"""
Shared backend utility module.

Exports:
  - normalize_card_uid(uid) -> str | None
      Canonical UID normalisation: strips whitespace, removes leading zeros,
      uppercases. Returns None for None input, "" for empty/whitespace input.

  - CardReaderState
      Thread-safe wrapper around the four Arduino / card-reader globals
      (arduino, arduino_bridge, card_reading_active, pending_student_id).
      Use the module-level singleton ``card_reader_state`` rather than
      instantiating this class directly.

  - card_reader_state
      Module-level CardReaderState singleton; import and use wherever the
      Arduino state is needed.
"""

import logging
import threading

logger = logging.getLogger("bangko.utils")


# ---------------------------------------------------------------------------
# UID normalisation
# ---------------------------------------------------------------------------

def normalize_card_uid(uid) -> str | None:
    """Return a canonical card UID string.

    Rules (applied in order):
      1. If *uid* is None → return None
      2. Strip leading/trailing whitespace
      3. Strip leading zeros
      4. Uppercase

    This is the single authoritative implementation that merges the two
    previous divergent versions from admin_dashboard.py (line 196) and
    api_server.py (line 144).  The admin version handled None; the API
    version did not.  This version handles both.

    Args:
        uid: Raw UID value from card reader (may be None, str, bytes, int).

    Returns:
        Normalised UID string, or None when uid is None, or '' when uid is empty/whitespace-only.
    """
    if uid is None:
        return None
    uid_str = str(uid).strip()
    if not uid_str:
        return ""
    return uid_str.lstrip("0").upper()


# ---------------------------------------------------------------------------
# Thread-safe card-reader state
# ---------------------------------------------------------------------------

class CardReaderState:
    """Thread-safe container for Arduino / card-reader globals.

    Replaces four unguarded module-level globals in admin_dashboard.py with a
    single threading.Lock-protected class.  All public attribute access MUST
    go through :meth:`get`, :meth:`set`, or :meth:`update` to guarantee
    thread safety.

    Attributes (private, access via get/set/update):
        arduino: Active serial.Serial connection object or None.
        arduino_bridge: Secondary bridge connection or None.
        card_reading_active (bool): Whether card-reading loop is running.
        pending_student_id (str | None): Student ID awaiting confirmation.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.arduino = None
        self.arduino_bridge = None
        self.card_reading_active = False
        self.pending_student_id = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str):
        """Return the current value of *key* under the lock.

        Args:
            key: One of 'arduino', 'arduino_bridge',
                 'card_reading_active', 'pending_student_id'.

        Returns:
            Current attribute value.

        Raises:
            AttributeError: If *key* is not a recognised state attribute.
        """
        with self._lock:
            return getattr(self, key)

    def set(self, key: str, value) -> None:
        """Set *key* to *value* under the lock.

        Args:
            key: Attribute name (see :meth:`get`).
            value: New value.
        """
        with self._lock:
            setattr(self, key, value)

    def update(self, **kwargs) -> None:
        """Atomically update multiple attributes in a single lock acquisition.

        Args:
            **kwargs: Attribute name → new value mappings.  All updates are
                applied within one lock acquisition to keep them atomic.

        Example::

            card_reader_state.update(
                card_reading_active=True,
                pending_student_id="S001",
            )
        """
        with self._lock:
            for k, v in kwargs.items():
                setattr(self, k, v)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Single shared CardReaderState instance.  Import this instead of
#: instantiating :class:`CardReaderState` directly.
card_reader_state = CardReaderState()
