"""Self-check that web_app now defines _decode_student_jwt (the QR 500 fix).

The QR routes called a function that was never defined -> NameError -> 500 on
every QR request. This confirms the function exists and round-trips a token.
"""
import os
import sys

# Minimal env so web_app imports without a live DB.
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("USE_SUPABASE", "false")

WEB = os.path.join(os.path.dirname(__file__), "..", "dashboard")
sys.path.insert(0, os.path.abspath(WEB))

import importlib


def demo():
    import web_app
    assert hasattr(web_app, "_decode_student_jwt"), "_decode_student_jwt still missing!"
    fn = web_app._decode_student_jwt

    # Missing token -> None (not a crash)
    assert fn(None) is None
    assert fn("") is None

    # Round-trip a real token
    import jwt as _jwt
    tok = _jwt.encode({"user_id": "202501"}, "test-secret", algorithm="HS256")
    payload = fn(tok)
    assert payload["user_id"] == "202501", payload

    # Tampered token -> None
    assert fn(tok + "x") is None

    print("QR _decode_student_jwt fix verified")


if __name__ == "__main__":
    demo()
