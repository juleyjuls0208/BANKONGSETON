# BankongSeton Infographic — Structured Content

**Topic:** BankongSeton (Bangko ng Seton) — digital canteen payment system
**Audience:** Students, Admins, Cashiers
**Layout:** dense-modules (6 panels)
**Style:** chalkboard
**Aspect:** portrait 9:16
**Language:** English

## Title (top, large hand-lettered chalk)

"Bangko ng Seton — Cashless Canteen, Three Sides, One System"

## Subtitle (small chalk, single line)

"RFID cards · Arduino POS · Google Sheets backend"

---

## Panel 1 — WHAT IT IS

**Label:** (1) THE SYSTEM

- Bangko ng Seton = digital canteen payment system for Seton School
- Replaces cash with RFID card taps
- Hardware: 2 Arduino R4 stations (Admin + Cashier)
- Backend: Python (Flask) + Google Sheets database
- Coverage-tested end-to-end

**Visual:** Hand-drawn icon: a card → terminal → canteen counter

---

## Panel 2 — STUDENT FLOW

**Label:** (2) FOR STUDENTS

- Tap your **Money Card** at the cashier reader
- LCD shows your current balance
- Tap your **ID Card** to confirm purchase
- Payment + attendance are auto-logged

**Result box:** "< 10 sec per txn · 100+ students/day"

**Visual:** Two small cards labeled "ID" and "₱" with arrows → checkmark

---

## Panel 3 — ADMIN FLOW

**Label:** (3) FOR ADMINS

- Register student → tap ID card once
- Link money card → tap ID, then tap money card
- Load balance → tap money card, enter amount
- Mark cards **Lost / Inactive** in the dashboard
- Web admin dashboard (login-protected) for reports

**Tech note:** "Admin Station runs `card_manager.py`"

**Visual:** Icon of a registration desk with a card and a keypad

---

## Panel 4 — CASHIER FLOW

**Label:** (4) FOR CASHIERS

- Run `bangko_backend.py` at the cashier PC
- Wait for student tap — no manual entry needed
- System reads money card → shows balance on LCD
- Student taps ID → payment processes automatically
- Audio alert on success or low balance (< ₱50)
- Every transaction auto-logs to Google Sheets

**Visual:** Hand-drawn POS terminal with screen showing "₱ balance" and a buzzer

---

## Panel 5 — SECURITY & FRAUD

**Label:** (5) SAFETY CHECKS

- **Dual-card** required (ID + Money) — can't pay with one card
- Card status: Active / Inactive / Lost
- Session login + secret-key auth on admin dashboard
- Full audit trail in Google Sheets
- Rate limit + transaction cap (default ₱500/txn)

**Badges (chalk circles):** [✓ dual-card] [✓ audit] [✓ lost-flag]

**Visual:** Sketch of a padlock with two card icons

---

## Panel 6 — THE STACK

**Label:** (6) UNDER THE HOOD

| Layer        | Tech                                  |
|--------------|---------------------------------------|
| Firmware     | C++ (.ino) — Admin + Cashier stations |
| Backend      | Python · Flask · gspread              |
| Database     | Google Sheets (5 sheets)              |
| Mobile       | React Native (student app)            |
| Auth         | Session + Flask secret key            |
| Tested       | Unit + integration coverage           |

**Footer chalk line (bottom):**
"Seton School · MIT · hardware + software + docs · v1.0"

---

## Decorative chalk doodles (placed in margins)

- Asterisks (*) and arrows around the title
- Small stars near badges
- A tiny coffee cup + lunch tray next to the cashier panel
- A school cap doodle next to the admin panel
- A chalk underline under the word "Cashless"
