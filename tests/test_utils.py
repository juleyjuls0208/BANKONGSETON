"""
Unit and concurrency tests for backend/utils.py.

Covers:
  - normalize_card_uid(): None, empty, whitespace, leading zeros, lowercase,
    already-clean inputs.
  - CardReaderState: get/set, update (atomic multi-field), and a 50-thread
    concurrency smoke test that asserts no exceptions and consistent final
    state.

Import style: ``from backend.utils import ...`` (project root on sys.path,
backend/ has no __init__.py but Python 3 supports namespace packages).
"""

import threading

import pytest

from backend.utils import CardReaderState, card_reader_state, normalize_card_uid


# ---------------------------------------------------------------------------
# normalize_card_uid tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestNormalizeCardUID:
    """Tests for the canonical normalize_card_uid() function."""

    def test_normalize_none(self):
        """None input returns None (passes through unchanged)."""
        assert normalize_card_uid(None) is None

    def test_normalize_empty(self):
        """Empty-string input returns empty string."""
        assert normalize_card_uid("") == ""

    def test_normalize_leading_zeros(self):
        """Leading zeros are stripped from the UID."""
        assert normalize_card_uid("00A1B2C3") == "A1B2C3"

    def test_normalize_lowercase(self):
        """Lowercase hex digits are converted to uppercase."""
        assert normalize_card_uid("a1b2c3") == "A1B2C3"

    def test_normalize_whitespace(self):
        """Leading and trailing whitespace is stripped."""
        assert normalize_card_uid("  A1B2  ") == "A1B2"

    def test_normalize_already_clean(self):
        """Already-normalised UIDs pass through unchanged."""
        assert normalize_card_uid("A1B2C3") == "A1B2C3"

    def test_normalize_whitespace_only(self):
        """Whitespace-only input returns empty string."""
        assert normalize_card_uid("   ") == ""

    def test_normalize_mixed_case_and_leading_zeros(self):
        """Combined: leading zeros + mixed case are both fixed."""
        assert normalize_card_uid("00a1b2c3") == "A1B2C3"


# ---------------------------------------------------------------------------
# CardReaderState tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCardReaderStateBasic:
    """Basic get/set/update tests for CardReaderState."""

    def setup_method(self):
        """Use a fresh instance for each test to avoid shared-state pollution."""
        self.state = CardReaderState()

    def test_get_default_card_reading_active(self):
        """Default value for card_reading_active is False."""
        assert self.state.get("card_reading_active") is False

    def test_get_default_pending_student_id(self):
        """Default value for pending_student_id is None."""
        assert self.state.get("pending_student_id") is None

    def test_get_default_arduino(self):
        """Default value for arduino is None."""
        assert self.state.get("arduino") is None

    def test_get_default_arduino_bridge(self):
        """Default value for arduino_bridge is None."""
        assert self.state.get("arduino_bridge") is None

    def test_get_set(self):
        """set() stores a value that get() can retrieve."""
        self.state.set("card_reading_active", True)
        assert self.state.get("card_reading_active") is True

    def test_set_pending_student_id(self):
        """set() works for string attributes."""
        self.state.set("pending_student_id", "S001")
        assert self.state.get("pending_student_id") == "S001"

    def test_set_arduino_object(self):
        """set() works for arbitrary object references (mocking a serial conn)."""
        fake_serial = object()
        self.state.set("arduino", fake_serial)
        assert self.state.get("arduino") is fake_serial

    def test_update_atomic(self):
        """update() sets multiple fields atomically in one lock acquisition."""
        self.state.update(
            card_reading_active=True,
            pending_student_id="S001",
        )
        assert self.state.get("card_reading_active") is True
        assert self.state.get("pending_student_id") == "S001"

    def test_update_all_four_fields(self):
        """update() covers all four managed attributes."""
        fake_a = object()
        fake_ab = object()
        self.state.update(
            arduino=fake_a,
            arduino_bridge=fake_ab,
            card_reading_active=True,
            pending_student_id="S999",
        )
        assert self.state.get("arduino") is fake_a
        assert self.state.get("arduino_bridge") is fake_ab
        assert self.state.get("card_reading_active") is True
        assert self.state.get("pending_student_id") == "S999"


# ---------------------------------------------------------------------------
# Concurrency test
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestCardReaderStateConcurrency:
    """Thread-safety smoke test — 50 concurrent readers and writers."""

    def test_concurrent_card_reads_state_consistency(self):
        """50 threads hammering set/get on the module singleton must not raise.

        Each thread:
          1. Calls card_reader_state.set('card_reading_active', True)
          2. Calls card_reader_state.get('card_reading_active')

        After all threads complete the final value must be True and no
        exceptions must have been raised.
        """
        errors = []

        def worker():
            try:
                card_reader_state.set("card_reading_active", True)
                card_reader_state.get("card_reading_active")
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Unexpected exceptions in worker threads: {errors}"
        assert card_reader_state.get("card_reading_active") is True

    def test_concurrent_mixed_operations(self):
        """50 threads mixing set/get/update must not raise or corrupt state."""
        fresh_state = CardReaderState()
        errors = []
        counter_lock = threading.Lock()
        completed = [0]

        def worker(index):
            try:
                if index % 3 == 0:
                    fresh_state.set("pending_student_id", f"S{index:03d}")
                elif index % 3 == 1:
                    fresh_state.update(card_reading_active=True, pending_student_id=f"S{index:03d}")
                else:
                    fresh_state.get("card_reading_active")
                    fresh_state.get("pending_student_id")
                with counter_lock:
                    completed[0] += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Unexpected exceptions in worker threads: {errors}"
        assert completed[0] == 50
