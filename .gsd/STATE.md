# GSD State

**Active Milestone:** M003 — Wireless Cashier Payment Terminal
**Active Slice:** S01 — Firmware WiFi Routing Fix
**Active Task:** None (planning complete — ready to execute S01)
**Phase:** Planning complete

## Milestone Registry
- ✅ **M001:** Operational Hardening & Feature Completion
- ✅ **M002:** Production Readiness & Deployment Stability
- 🔄 **M003:** Wireless Cashier Payment Terminal

## Recent Decisions
- D028: Arduino WiFi routing split by prefix (two httpPost helpers by prefix in deliver())
- D029: Arduino heartbeat as dual-purpose keep-alive (30s POST to /api/arduino/heartbeat)
- D030: Phone NFC token resolution in cashier_routes.py (not cross-process call to api_server.py)
- D031: arduinoConnected honors both serial and WiFi states (WiFi path sets same flag via socket event)

## Blockers
- None

## Next Action
Execute S01: Firmware WiFi Routing Fix.
Read `.gsd/milestones/M003/M003-CONTEXT.md` and `M003-ROADMAP.md` for full context.
Core change: split `deliver()` in `arduino/bankongseton_rfid/bankongseton_rfid.ino` into two `httpPost` helpers — `httpPostCard(uid)` → `POST /api/arduino/card-read {"uid": uid}` and `httpPostNFC(token)` → `POST /api/nfc/tap {"token": token}`. Verify firmware compiles; confirm card read fires `card_read` event in cashier UI.
