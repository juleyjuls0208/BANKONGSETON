"""Self-check for PIN + one-device-per-account login logic.

Tests the pure decision logic (first-login sets PIN+device, returning login
verifies PIN and enforces the bound device) without a live Sheets/Supabase
backend. Run: python backend/tests/test_pin_device_login.py
"""
from werkzeug.security import generate_password_hash, check_password_hash


def decide_login(auth_row, pin, device_id):
    """Mirror of api_server.login()'s PIN+device branch.

    auth_row: dict from student_auth table, or None if never set up.
    Returns (status_code, action) where action is one of:
      'set'    -> create/bind PIN+device (first login)
      'ok'     -> allow (PIN matches, device matches)
      'bind'   -> allow + bind device (PIN existed, no device yet)
      'bad_pin', 'other_device' -> reject
    """
    first_login = auth_row is None or not str(auth_row.get("PinHash", "")).strip()
    if first_login:
        return 200, "set"
    if not check_password_hash(str(auth_row.get("PinHash", "")), pin):
        return 401, "bad_pin"
    bound = str(auth_row.get("DeviceId", "")).strip()
    if bound and bound != device_id:
        return 409, "other_device"
    if not bound:
        return 200, "bind"
    return 200, "ok"


def demo():
    h = generate_password_hash("1234")

    # 1. First login ever: no row -> set PIN + bind device
    assert decide_login(None, "1234", "phoneA") == (200, "set")

    # 2. First login: row exists but empty PIN -> still first login
    assert decide_login({"PinHash": "", "DeviceId": ""}, "5678", "phoneA") == (200, "set")

    # 3. Returning, correct PIN, same device -> ok
    assert decide_login({"PinHash": h, "DeviceId": "phoneA"}, "1234", "phoneA") == (200, "ok")

    # 4. Returning, wrong PIN -> reject 401 (even on the right device)
    assert decide_login({"PinHash": h, "DeviceId": "phoneA"}, "0000", "phoneA") == (401, "bad_pin")

    # 5. Returning, correct PIN, DIFFERENT device -> reject 409 (one device only)
    assert decide_login({"PinHash": h, "DeviceId": "phoneA"}, "1234", "phoneB") == (409, "other_device")

    # 6. PIN set but device never bound (e.g. after admin reset-device) -> bind new phone
    assert decide_login({"PinHash": h, "DeviceId": ""}, "1234", "phoneB") == (200, "bind")

    # 7. Wrong PIN takes precedence over device check
    assert decide_login({"PinHash": h, "DeviceId": "phoneA"}, "9999", "phoneB") == (401, "bad_pin")

    print("all PIN + one-device login checks passed")


if __name__ == "__main__":
    demo()
