Create a portrait (9:16) high-density infographic on a CLASSROOM CHALKBOARD. Six labeled information modules in a 2-column x 3-row dense grid, plus a top title block and a bottom footer strip. Style is hand-drawn chalk on a dark green-black chalkboard (#1C2B1C). EVERY line, frame, and label looks like it was drawn with chalk — imperfect, slightly smudged, with chalk dust.

## Background
- Color: dark green-black chalkboard (#1C2B1C)
- Texture: realistic chalkboard with subtle scratches, faint eraser streaks, dust specks
- NOT a black screen, NOT a digital gradient — must look like an actual classroom blackboard

## Typography
- All headings: hand-lettered chalk in WHITE (#F5F5F5), slightly thick, with visible chalk grain
- Body text: smaller chalk lettering in white
- Accent text: CHALK YELLOW (#FFE566) and CHALK BLUE (#66B3FF)
- One monospace-style chalk block for the stack table
- Imperfect baseline — letters slightly wavy, not perfectly aligned

## Color palette
- Background: #1C2B1C chalkboard green-black
- Primary text: #F5F5F5 chalk white
- Accent yellow: #FFE566 (highlights, badges, "new" tags)
- Accent blue: #66B3FF (links, arrows, secondary headings)
- Accent pink: #FF9999 (warnings or numbers)
- Accent orange: #FFB366 (cashier / money)
- Accent green: #90EE90 (success checkmarks)

## Layout

### Top — Title block (full width)
- Main title (large hand-lettered chalk, white): "Bangko ng Seton — Cashless Canteen, Three Sides, One System"
- Subtitle below (smaller yellow chalk): "RFID cards · Arduino POS · Google Sheets backend"
- Decorative asterisks and small chalk stars on both sides of the title
- A wavy chalk underline beneath "Cashless"

### Body — 2 columns x 3 rows = 6 dense modules
Each module is a hand-drawn rectangle with a sketchy dashed or solid chalk border. Each module has a circled number (1)–(6) in a yellow chalk circle at the top-left corner.

**Module (1) THE SYSTEM — top-left**
- Heading: "WHAT IT IS"
- Content:
  - "Digital canteen payment for Seton School"
  - "Replaces cash with RFID taps"
  - "2 Arduino R4 stations (Admin + Cashier)"
  - "Python Flask + Google Sheets"
  - "Coverage-tested end-to-end"
- Visual: small chalk sketch of a card → terminal → canteen tray

**Module (2) FOR STUDENTS — top-right**
- Heading: "STUDENT FLOW"
- Content:
  - "1. Tap Money Card at cashier"
  - "2. LCD shows your balance"
  - "3. Tap ID Card to confirm"
  - "4. Payment + attendance auto-log"
- Result chalk box (yellow): "< 10 sec/txn · 100+ students/day"
- Visual: two tiny chalk cards labeled "ID" and "₱" with a curved arrow between them

**Module (3) FOR ADMINS — middle-left**
- Heading: "ADMIN FLOW"
- Content:
  - "Register → tap ID card"
  - "Link money card → ID, then money"
  - "Load balance → tap money card"
  - "Mark Lost / Inactive in dashboard"
  - "Web admin panel (session login)"
- Tech-note (small blue chalk): "runs `card_manager.py`"
- Visual: sketch of a school cap above a card + keypad

**Module (4) FOR CASHIERS — middle-right**
- Heading: "CASHIER FLOW"
- Content:
  - "Run `bangko_backend.py` and wait"
  - "Student taps money card → balance"
  - "Student taps ID → auto-charges"
  - "Audio alert on success / low ₱"
  - "All logs → Google Sheets"
- Visual: hand-drawn POS terminal with a tiny screen labeled "₱ balance" and a small speaker

**Module (5) SAFETY CHECKS — bottom-left**
- Heading: "SECURITY"
- Content:
  - "Dual-card required (ID + Money)"
  - "Card status: Active / Inactive / Lost"
  - "Session login + secret-key auth"
  - "Full audit trail in Sheets"
  - "Txn cap ₱500 · low-balance alert ₱50"
- Three small chalk-circle badges in a row: [✓ dual-card] [✓ audit] [✓ lost-flag]
- Visual: chalk padlock with two card icons

**Module (6) UNDER THE HOOD — bottom-right**
- Heading: "THE STACK"
- A compact 2-column chalk table (drawn, not typed):
  - Hardware | Arduino R4 · RFID-RC522
  - Firmware | C++ (.ino) — Admin + Cashier
  - Backend  | Python · Flask · gspread
  - Database | Google Sheets (5 sheets)
  - Mobile   | React Native (student app)
  - Auth     | Session + Flask secret key
  - Tests    | Unit + integration coverage
- Small green checkmark next to "Tests"

### Bottom — Footer strip (full width, thin)
- A thin chalk line, then small chalk text:
  "Seton School · MIT · hardware + software + docs · v1.0"
- Tiny chalk doodles on each end: a coffee cup (left) and a school cap (right)

## Decorative chalk doodles (in margins and corners)
- Small chalk stars sprinkled around the title
- Curved chalk arrows connecting module (1) → (2) → (3) → (4)
- A tiny lunch tray doodle next to module (4)
- A tiny lunch tray doodle next to module (4)
- A chalk-drawn "₱" peso symbol floating between modules (3) and (4)

## Style rules (strict)
- EVERY line must look like chalk — slightly broken, with grain, never perfectly straight
- NO clean digital rectangles, NO drop shadows, NO glossy gradients
- NO photorealistic elements
- Wooden frame border around the entire chalkboard is OPTIONAL — if present, must be a rough brown chalk frame
- Slight chalk dust under each heading
- Numbers (1)–(6) inside hand-drawn yellow chalk circles
- Checkmarks in green chalk
- Code/command names in monospace-style chalk (like `bangko_backend.py`)

## Critical: Visual style ONLY, not the contents of the reference
The reference style is a chalkboard infographic with 6 modules, hand-lettered text, yellow and blue chalk accents, and small chalk doodles. Copy that VISUAL STYLE for the Bangko ng Seton content above. Do NOT reproduce any text, code, brand names, or content from the reference image.
