---
title: Scaffold standalone app.py and launcher
one-liner: Create standalone cashier app.py on port 5010 with batch launcher
observability_surfaces:
  - flask logs
  - socketio connection events
---

# Task T01: Scaffold standalone app.py and launcher

## Summary
I created a separate standalone application specifically for the cashier POS terminal, which runs independently from the admin dashboard. 
- Created `backend/cashier_app/app.py` listening on port 5010 with `flask` and `flask_socketio`.
- Added placeholder global state properties `app.pending_qr_token` and `app.arduino_last_heartbeat`.
- Wrote a standard index route `/` to verify server functionality.
- Created `run_cashier.bat` inside the project root for starting the application easily on Windows.
- Copied `.env.example` to `.env` to test config load properly.

## Verification Evidence
| Command | Exit Code | Verdict | Duration |
| ------- | --------- | ------- | -------- |
| `python backend/cashier_app/app.py` & `curl http://127.0.0.1:5010/` | `0` | ✅ pass | 2s |
| Check `run_cashier.bat` content | `0` | ✅ pass | ~0s |

All must-haves met. The application listens and responds on the requested port without crashing.

## Diagnostics
- Standard Flask logs to stdout/stderr.
- SocketIO connection events log to standard output.
- Start using `run_cashier.bat` to see output in the Windows console.