# Bangko ng Seton — User Guide

Bangko ng Seton is a digital canteen payment system for schools. Students pay using their phone (QR code) or a physical RFID card. All money is digital — no cash changes hands at the counter.

The system has two interfaces:

| Interface | Who Uses It |
|-----------|-------------|
| **Cashier Terminal** (POS) | Canteen staff — takes payments at the counter |
| **Admin Dashboard** | School administrators — manages students, cards, and finances |

---

## How It Works

1. Parents load money into a student's account (handled by admin/finance staff).
2. Students buy food at the canteen. They pay by:
   - **QR Code** — scanning a code on the cashier's screen with their phone app
   - **RFID Card** — tapping a physical money card on the reader at the counter
3. The amount is deducted from their balance instantly.
4. Students can check their balance and transaction history on their phone app anytime.

All data is stored in Google Sheets, so administrators can view and audit everything from anywhere.

---

## Part 1: The Cashier Terminal

The cashier uses a web-based point-of-sale screen to process purchases. It runs in a browser on a computer or tablet at the canteen counter.

### Logging In

When you open the cashier terminal, you'll see a login screen. Enter your username and password. Each cashier has their own account, so all transactions are traceable to who processed them.

### The Main Screen

After logging in, you see three panels:

**Products Panel (left)** — All available canteen items, color-coded by category (meals, drinks, snacks, etc.). Tap any product to add it to the current sale.

**Cart Panel (center)** — Shows what's being purchased right now. Each item shows its name, price, quantity, and subtotal. You can adjust quantities or remove items before completing the sale.

**Payment Panel (right)** — Where the payment happens. Shows a QR code for phone payments, or waits for a card tap. Status messages tell you what's happening at each step.

The top bar shows "Canteen Ledger — Cashier Terminal," a WiFi status indicator, and a logout button.

### Making a Sale with QR Code

This is the most common method — the student pays using their phone.

1. **Build the cart.** Tap product buttons to add items. Tap an item multiple times to increase quantity.
2. **Show the QR code.** The system generates a QR code on the payment panel.
3. **Student scans and confirms.** The student opens their BankongSeton app, scans the QR code, reviews the items and total, then taps "Confirm Payment."
4. **Done.** The screen confirms payment, the cart clears, and you're ready for the next customer.

The whole process takes about 5-10 seconds per student.

### Making a Sale with a Card

If a student has a physical RFID money card:

1. **Build the cart** the same way.
2. **Student taps their card** on the reader at the counter. It beeps and reads the card.
3. **Done.** The amount is deducted automatically. The cart clears.

No card? No problem — the student can always use their phone with the QR method instead.

### Canceling

If you need to cancel a sale before it's completed, click **Cancel Sale**. The cart clears and you can start fresh.

### What If the Internet Goes Down?

The cashier terminal keeps working. A banner appears letting you know it's offline, but you can continue selling. Transactions are saved locally and sync automatically when the connection comes back. No receipts are lost.

---

## Part 2: The Admin Dashboard

The admin dashboard is where staff manage students, cards, money, and view all financial activity.

### Logging In

The dashboard has two types of accounts:

- **Finance Staff** — can view everything, enroll students, load money, and export reports. This is for day-to-day operations.
- **Administrator** — can do everything finance staff can, plus manage cashier accounts, handle fraud alerts, and issue/replace cards. This is for system management.

### The Dashboard

The home screen gives you an at-a-glance view:

- **Total enrolled students**
- **Transactions today** — how many purchases have happened
- **Daily revenue** — total amount collected today
- **Low balance alerts** — students running low on funds
- **Recent activity** — a live feed of the latest transactions

### Managing Students

The **Students** page is where you handle the full student lifecycle.

#### Enrolling a New Student
Click **Enroll Student**, enter their student ID and name, and save. They now have an account and can receive money.

#### Searching
Use the search bar to find a student by name or ID. Click any student to see their full profile: current balance, transaction history, card status, and budget settings.

#### Loading Money
When a parent gives money to load onto a student's account:
1. Find the student
2. Click **Load Balance**
3. Enter the amount (in Philippine Pesos)
4. Add a note (e.g., "Weekly allowance — March 24")
5. Confirm

The balance updates immediately, and the transaction is logged permanently.

### Managing Cards

Every student can optionally have a physical RFID card. This is managed from the Students page.

#### Issuing a New Card
Click **Register Card** next to a student, then tap the physical card on the USB card reader connected to the admin computer. The card is now linked — the student can use it at the canteen.

#### Reporting a Lost Card
If a student loses their card, click **Report Lost**. The card is immediately deactivated — nobody can use it. The student's money is preserved.

#### Replacing a Lost Card
After reporting a card lost, click **Replace Card** and register a new one. The balance transfers automatically from the old card to the new one.

### Transactions

The **Transactions** page shows every financial event in the system: sales, balance loads, refunds, and voids.

You can filter by:
- Date range
- Transaction type (sale, load, void)
- Specific student

#### Voiding a Transaction
If a mistake was made (wrong item, wrong student), an administrator can void a transaction. The money is refunded to the student's balance. Voids are permanent and logged.

#### Exporting
Click **Export** to download transactions as a CSV file. Open it in Excel or Google Sheets for accounting, reconciliation, or reporting.

### Fraud Alerts

The system automatically detects suspicious activity and raises alerts:

- **Rapid purchases** — same card used multiple times in quick succession
- **Unusually large transactions**
- **Negative balances**

Administrators review alerts, mark them as resolved, or suspend a card if fraud is suspected. A suspended card cannot be used for payment until an administrator unsuspends it.

### Products

The product catalog (what's sold at the canteen) is managed in Google Sheets. Any changes — adding items, updating prices, changing categories — appear in the cashier terminal automatically within 30 seconds.

### Cashier Accounts

Administrators manage who can use the cashier terminal. You can add new cashiers, deactivate old ones, and reset passwords.

### Reports

The **Reports** page provides downloadable exports:
- **Full transaction log** — filtered by date
- **Student list** — all students with current balances
- **Student statement** — monthly summary for a specific student, showing every transaction, opening and closing balance, and spending by category. Useful for parents.

---

## Full Workflow Example

Here's what a typical day looks like:

**Morning — Setup**
- Administrator opens the admin dashboard and cashier terminal
- Verifies the Arduino card reader shows a green WiFi badge (connected)

**During Canteen Hours**
- Students line up, pick their food
- Cashier taps the items on screen, generates a QR code
- Student scans with their phone and confirms — payment done in seconds
- Some students tap their card instead — even faster

**Throughout the Day**
- Finance staff load money onto accounts as parents send funds
- Administrator checks the dashboard periodically for any fraud alerts

**End of Day**
- Finance staff exports the day's transactions as CSV
- Compares total revenue against money loaded
- Done. No cash to count, no discrepancies to hunt down.

---

## Key Concepts

**Where is the money?** All balances are stored in Google Sheets. There is no actual cash in the system — just digital balances that students spend against.

**What if a student has no money?** The system won't allow a purchase that exceeds the student's balance. The cashier will see a declined message.

**Can a student pay with both card and phone?** Yes. The QR code and the card are two ways to access the same account. The student doesn't need both.

**Who sees what?** Cashiers only see the POS screen — they can't view student balances or manage accounts. Finance staff can view everything and load money. Only administrators can void transactions, manage cards, and handle fraud alerts.
