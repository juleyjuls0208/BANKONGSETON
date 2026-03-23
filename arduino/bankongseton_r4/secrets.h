// Copy this file to secrets.h and fill in your values.
// secrets.h is gitignored — never commit real credentials.

#ifndef SECRETS_H
#define SECRETS_H

// WiFi network credentials
// Comment these out to disable WiFi and skip the ~21-second retry delay.
// Uncomment and re-flash to enable wireless NFC tap delivery.
#define SECRET_SSID "LNC_Family_MESH1"
#define SECRET_PASS "PLDTWifi5678901234!"

// Flask server on the school LAN (no trailing slash)
// Wireless mode (WiFi enabled above): use port 5003 — dashboard has /api/nfc/tap
// USB serial mode (WiFi commented out): FLASK_HOST is unused, value doesn't matter
#define FLASK_HOST "192.168.68.104:5010"

// Must match ARDUINO_API_KEY in Flask .env
#define SECRET_API_KEY "testkey123"

// HEARTBEAT_INTERVAL_MS (30000 ms) is defined as a constant in bankongseton_rfid.ino
// (not here) — see the HTTP tuning section. S04 will add heartbeat POST logic there.

#endif