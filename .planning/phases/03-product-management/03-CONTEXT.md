# Phase 3: Product Management - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Admin can maintain the canteen menu in the dashboard (add, edit, deactivate products stored in a
dedicated Google Sheets Products sheet), and the cashier POS displays all active products and
processes multi-item selections as a single transaction charged to the student's RFID card.

Creating the student transaction history view, itemized receipts, and notifications are Phase 4.
NFC payment flow is Phase 5.

</domain>

<decisions>
## Implementation Decisions

### Admin Product UI
- Product management lives on a **dedicated page** in the admin dashboard navigation (not a section of the home page)
- Product list is displayed as a **table with inline actions** (Edit/Deactivate per row)
- Editing a product uses **inline row editing** — user clicks a field to edit it in-place, saves on blur/Enter; no modal or separate page
- Inline edits **auto-save to Google Sheets** immediately — no explicit Save button needed
- Successful saves show a **brief toast notification** (e.g. "Saved")
- "Add product" form is **always visible at the top of the page** — not behind a button or modal
- Form validation errors are shown **inline** — red border on empty/invalid fields when the user attempts to submit
- Deactivated products remain visible in the admin table (not hidden); the table shows **all products with a status toggle column**
- A **Status column** with an Active/Inactive badge visually distinguishes active from deactivated products

### Category System
- Categories are a **fixed predefined list**: Food, Drinks, Snacks, Other
- Admin selects from this list when adding/editing a product (dropdown)
- On the cashier POS, categories appear as **filter tabs** at the top of the product grid
- The **"All" tab is the default** view — shows all active products on POS load

### POS Grid & Checkout
- Products display as a **fixed uniform tile grid** — same size for all products, each tile shows product name and price
- Cashier **taps a tile to add it to the order**; tapping the same tile again adds another unit (quantity stacks)
- The running order (selected items and running total) appears in a **sidebar on the right** of the grid
- Checkout flow: cashier taps a **Charge button**, then the student taps their RFID card — the transaction commits on card tap
- Transaction is submitted as a **single charge** for the total of all selected items

### Deactivate Behavior
- Deactivating a product is a **soft deactivate** — the product row stays in Google Sheets with an inactive status flag; admin can reactivate at any time
- Admin deactivates via a **toggle switch in the table row** — one tap, no confirmation dialog required
- Deactivated products are **completely hidden from the cashier POS grid** — cashier never sees them
- In the admin table, deactivated rows have a **Status column showing Inactive** (badge or icon) and the row is grayed out

### Claude's Discretion
- Exact tile size, color palette, and typography on the POS grid
- Loading/spinner states during Sheets API calls
- Error state handling (e.g. failed save, card tap fails mid-checkout)
- Exact visual styling of the toast notification
- How the sidebar order panel handles removing an item from the order (e.g. tap to decrement or remove)

</decisions>

<specifics>
## Specific Ideas

- No specific UI references provided — standard clean dashboard and POS aesthetic is fine
- The system uses Google Sheets as the database; the Products sheet needs an active/inactive flag column to support soft deactivate

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-product-management*
*Context gathered: 2026-02-26*
