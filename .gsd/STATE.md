# GSD State

**Active Milestone:** M003 — Wireless Cashier Payment Terminal
**Active Slice:** none (S04 complete — all M003 slices done)
**Phase:** awaiting hardware UAT
**Requirements Status:** 5 active · 19 validated · 0 deferred · 2 out of scope

## Milestone Registry
- ✅ **M001:** Operational Hardening & Feature Completion
- ✅ **M002:** Production Readiness & Deployment Stability
- 🔄 **M003:** Wireless Cashier Payment Terminal — all 4 slices complete at contract level; hardware UAT gate remaining

## Recent Decisions
- D036: Heartbeat timer block placed before NFC early-exit in loop() — fires during idle, not gated by if (!found) return

## Blockers
- None

## Next Action
All M003 slices done at contract level. Hardware UAT required to close the milestone:
1. Flash updated firmware → confirm #wifiBadge turns green within 30s
2. WiFi drop/reconnect test — badge recovers without reboot
3. 30-minute powerbank soak — Arduino stays powered
See `.gsd/milestones/M003/slices/S04/S04-UAT.md` for the full UAT script.
