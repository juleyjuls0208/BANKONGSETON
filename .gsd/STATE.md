# GSD State

**Active Milestone:** M004 — NFC Phone Payment Fix
**Active Slice:** S01 — Firmware APDU Retry
**Active Task:** none (planning complete, ready to execute)
**Phase:** Executing

## Recent Decisions

- D037: APDU inDataExchange wrapped in retry loop (APDU_MAX_RETRIES=3, APDU_RETRY_DELAY_MS=150)
- D038: complete_sale_nfc Money Accounts lookup aligns to D032 (direct string, not normalize_card_uid)

## Blockers

- None

## Next Action

Execute S01: add `APDU_MAX_RETRIES 3` and `APDU_RETRY_DELAY_MS 150` constants to `arduino/bankongseton_rfid/bankongseton_rfid.ino`, wrap the `inDataExchange` call in a retry loop (reset responseLength=60 before each attempt; break on success; delay between attempts only), update Serial diagnostic output to show attempt N/3, write `scripts/verify-m004.sh`, commit.
