# Phase 3: Product Management - Research

**Researched:** 2026-02-26
**Domain:** Flask/Jinja2 admin UI, Google Sheets CRUD, cashier POS frontend (vanilla JS)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Admin Product UI:**
- Product management lives on a **dedicated page** in the admin dashboard navigation (not a section of the home page)
- Product list is displayed as a **table with inline actions** (Edit/Deactivate per row)
- Editing a product uses **inline row editing** — user clicks a field to edit it in-place, saves on blur/Enter; no modal or separate page
- Inline edits **auto-save to Google Sheets** immediately — no explicit Save button needed
- Successful saves show a **brief toast notification** (e.g. "Saved")
- "Add product" form is **always visible at the top of the page** — not behind a button or modal
- Form validation errors are shown **inline** — red border on empty/invalid fields when the user attempts to submit
- Deactivated products remain visible in the admin table (not hidden); the table shows **all products with a status toggle column**
- A **Status column** with an Active/Inactive badge visually distinguishes active from deactivated products

**Category System:**
- Categories are a **fixed predefined list**: Food, Drinks, Snacks, Other
- Admin selects from this list when adding/editing a product (dropdown)
- On the cashier POS, categories appear as **filter tabs** at the top of the product grid
- The **"All" tab is the default** view — shows all active products on POS load

**POS Grid & Checkout:**
- Products display as a **fixed uniform tile grid** — same size for all products, each tile shows product name and price
- Cashier **taps a tile to add it to the order**; tapping the same tile again adds another unit (quantity stacks)
- The running order (selected items and running total) appears in a **sidebar on the right** of the grid
- Checkout flow: cashier taps a **Charge button**, then the student taps their RFID card — the transaction commits on card tap
- Transaction is submitted as a **single charge** for the total of all selected items

**Deactivate Behavior:**
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

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PROD-01 | Admin can add a canteen product (name, price, category) | Always-visible add form at top of products.html; POST /api/products/add; append_row to Products sheet |
| PROD-02 | Admin can edit an existing product (name, price, category) | Inline row editing in table; PATCH/POST /api/products/update; gspread batch_update or update range |
| PROD-03 | Admin can delete/deactivate a product | Toggle switch in table row; POST /api/products/toggle-status; update_cell on Active column (col 6) |
| PROD-04 | Cashier POS displays all active products in a grid with name and price | /cashier/api/products already returns all products; frontend filters p.active === true; tile grid already styled |
| PROD-05 | Products are stored in Google Sheets (a dedicated Products sheet) | Products sheet schema already exists (ID, Name, Category, Price, ImageURL, Active, DateAdded); needs Active column verification |
| PROD-06 | Cashier can select multiple products and process them as one transaction | Cart accumulation and complete-sale endpoint already implemented; needs wiring to new product data and UI polish |
</phase_requirements>

---

## Summary

This phase is largely **already implemented in skeleton form** — the codebase has more working code than the requirements suggest. The `/products` admin page (`products.html`), `/api/products/list`, `/api/products/update`, and `/api/products/delete` endpoints all exist in `admin_dashboard.py`. The cashier POS (`cashier_index.html`) already has a product grid, category filter tabs, cart sidebar, and checkout flow. The `complete-sale` endpoint in `cashier_routes.py` includes retry+rollback transaction logic.

**The gap between requirements and reality is a UX redesign, not a feature build.** The existing admin page uses a card grid with a modal for editing — this must be replaced with a table with inline row editing, an always-visible add form, and a toggle switch for deactivation. The existing POS is functionally close but the category labels in `products.json` (Food, Drinks, Stationery, Others) diverge from the locked decisions (Food, Drinks, Snacks, Other). The Google Sheets Products sheet schema must be verified/created.

**Primary recommendation:** Audit what exists, replace the admin UI components that conflict with locked decisions, verify the Google Sheets Products sheet schema, then verify the end-to-end flow works. Estimated scope: ~4–5 plan files.

---

## Existing Codebase Audit

### What Already Works (DO NOT REBUILD)

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| `/products` route | `admin_dashboard.py:294` | EXISTS | Renders `products.html` |
| `GET /api/products/list` | `admin_dashboard.py:302` | EXISTS | Returns all products (active + inactive) |
| `POST /api/products/update` | `admin_dashboard.py:332` | EXISTS | Upsert by ID (create or update) |
| `POST /api/products/delete` | `admin_dashboard.py:381` | EXISTS | Soft deactivate (sets Active=FALSE) |
| `GET /cashier/api/products` | `cashier_routes.py:152` | EXISTS | Returns all products; frontend filters active ones |
| `POST /cashier/api/process-sale` | `cashier_routes.py:189` | EXISTS | Initiates sale, stores pending_transaction in session |
| `POST /cashier/api/complete-sale` | `cashier_routes.py:229` | EXISTS | Deducts balance, logs transaction, retry+rollback |
| Cashier POS grid + sidebar + cart | `cashier_index.html` | EXISTS | Tile grid, category tabs, cart, checkout modal |
| Products.html admin page | `products.html` | EXISTS | But wrong UI pattern — uses modal not inline edit |

### What Does NOT Exist (Must Build)

| Gap | Description |
|-----|-------------|
| Always-visible "Add Product" form | Currently behind a modal; must be a persistent top-of-page form |
| Inline row editing table | Currently a card grid with modal; must be HTML table with editable cells |
| Auto-save on blur/Enter | Currently requires clicking Save in modal |
| Toast notification on save | No toast — currently uses `alert()` on success |
| Toggle switch for deactivate | Currently no toggle; delete button via modal |
| Grayed-out inactive rows | No visual distinction for inactive products in admin |
| Status badge column (Active/Inactive) | Not in current table layout |
| Category list fix (Snacks/Other) | Current code has "Stationery" and "Others"; must be Food/Drinks/Snacks/Other |
| Products sheet "Active" column verification | Must confirm Google Sheets has Active column (col 6); schema may need setup |

### What Needs to Be Replaced (Not Extended)

| Component | Replace With | Reason |
|-----------|-------------|--------|
| `products.html` card grid + modal | Table with inline editing + always-visible add form | Locked decision |
| Category options (Stationery/Others) | Food, Drinks, Snacks, Other | Locked decision |
| `alert()` on success | Toast notification | Locked decision |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | Already installed (2.x) | Server-side routing, session, templates | Already in use; no change |
| gspread | Already installed (6.x) | Google Sheets read/write | Already in use; pattern established |
| Bootstrap 5.3 | CDN (already in products.html) | UI components: table, badge, toggle, toast | Already loaded via CDN |
| Bootstrap Icons 1.11 | CDN (already in products.html) | Icons for status badges, buttons | Already loaded |
| Vanilla JS (no framework) | — | Frontend logic | Consistent with existing cashier_index.html |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Socket.IO 4.5.4 | CDN (already in cashier_index.html) | Real-time card tap events for checkout | Already wired; cashier_index.html:95 |
| Bootstrap Toast component | Part of Bootstrap 5.3 | "Saved" notification after inline edit | Use instead of `alert()` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Inline contenteditable | `<input>` inside `<td>` | `<input>` is simpler and works consistently; contenteditable has cross-browser quirks |
| Bootstrap Toast | Custom CSS toast | Bootstrap Toast already available; no custom code needed |
| gspread batch_update | update_cell per field | batch_update reduces API calls for multi-field edits; prefer for row updates |

**Installation:** No new packages required. All dependencies already installed system-wide.

---

## Architecture Patterns

### Recommended File Structure Changes

```
backend/
└── dashboard/
    └── templates/
        └── products.html    ← REWRITE (table + inline edit + add form + toast)
    └── admin_dashboard.py   ← ADD: /api/products/add endpoint
                               MODIFY: /api/products/update (handle partial field edits)
                               MODIFY: /api/products/delete → /api/products/toggle-status
    └── cashier/
        └── templates/
            └── cashier_index.html  ← MODIFY: update category list; verify active filter
```

### Pattern 1: Inline Row Editing (HTML table + contenteditable `<input>`)

**What:** Each `<td>` in the product table contains either a display element or an `<input>`/`<select>`. User clicks a cell to activate editing. On `blur` or `Enter` keypress, auto-save fires.

**When to use:** For PROD-02 (edit existing product inline).

**Key implementation detail:** Do NOT use `contenteditable`. Use hidden `<input>` elements that swap with display text on click. This avoids `contenteditable` paste/format issues.

```html
<!-- Pattern: display span + hidden input, toggled on click -->
<td class="editable-cell" data-field="name" data-id="{{ product.id }}">
  <span class="cell-display">{{ product.name }}</span>
  <input class="cell-input d-none form-control form-control-sm"
         value="{{ product.name }}"
         onblur="saveField(this)"
         onkeydown="if(event.key==='Enter') this.blur()">
</td>
```

```javascript
// Auto-save on blur
async function saveField(input) {
    const td = input.closest('td');
    const productId = td.dataset.id;
    const field = td.dataset.field;
    const value = input.value.trim();
    
    const payload = { id: productId, [field]: value };
    const resp = await fetch('/api/products/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    
    if (resp.ok) {
        td.querySelector('.cell-display').textContent = value;
        showToast('Saved');
    } else {
        showToast('Save failed', 'danger');
    }
    // Swap back to display mode
    input.classList.add('d-none');
    td.querySelector('.cell-display').classList.remove('d-none');
}
```

### Pattern 2: Bootstrap Toast for Save Confirmation

**What:** Lightweight non-blocking notification. Bootstrap 5.3 provides `bootstrap.Toast` class.

**When to use:** Every auto-save success or error (PROD-01, PROD-02).

```html
<!-- Place once in body, near closing </body> tag -->
<div class="toast-container position-fixed bottom-0 end-0 p-3">
    <div id="saveToast" class="toast align-items-center text-bg-success border-0" role="alert">
        <div class="d-flex">
            <div class="toast-body" id="toastMessage">Saved</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    </div>
</div>
```

```javascript
function showToast(message, type = 'success') {
    const toastEl = document.getElementById('saveToast');
    document.getElementById('toastMessage').textContent = message;
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    const toast = new bootstrap.Toast(toastEl, { delay: 2000 });
    toast.show();
}
```

### Pattern 3: Toggle Switch for Soft Deactivate

**What:** Bootstrap `form-check form-switch` renders as a toggle. `change` event fires auto-save.

**When to use:** PROD-03 (deactivate/reactivate product).

```html
<td>
  <div class="form-check form-switch">
    <input class="form-check-input" type="checkbox" 
           id="toggle-{{ p.id }}" 
           {{ 'checked' if p.active else '' }}
           onchange="toggleStatus('{{ p.id }}', this.checked)">
  </div>
</td>
```

```javascript
async function toggleStatus(productId, active) {
    const resp = await fetch('/api/products/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ id: productId, active: active })
    });
    if (resp.ok) {
        // Gray out the row if deactivated
        const row = document.querySelector(`tr[data-id="${productId}"]`);
        row.classList.toggle('table-secondary', !active);
        const badge = row.querySelector('.status-badge');
        badge.textContent = active ? 'Active' : 'Inactive';
        badge.className = `badge status-badge ${active ? 'bg-success' : 'bg-secondary'}`;
        showToast(active ? 'Product activated' : 'Product deactivated');
    }
}
```

### Pattern 4: Always-Visible Add Form at Top of Page

**What:** A persistent `<form>` section above the product table. Does not require button click to reveal.

**Key detail:** On submit, generate a new product ID (timestamp-based `PROD-{timestamp}`) client-side, POST to `/api/products/add` (or `/api/products/update` with new ID), then prepend new row to table without page reload.

```javascript
async function addProduct(event) {
    event.preventDefault();
    const form = event.target;
    const nameInput = form.querySelector('#newName');
    const priceInput = form.querySelector('#newPrice');
    const catInput = form.querySelector('#newCategory');
    
    // Validation: red border on empty
    let valid = true;
    [nameInput, priceInput].forEach(el => {
        if (!el.value.trim()) {
            el.classList.add('is-invalid');
            valid = false;
        } else {
            el.classList.remove('is-invalid');
        }
    });
    if (!valid) return;
    
    const newId = 'PROD-' + Date.now();
    const payload = {
        id: newId,
        name: nameInput.value.trim(),
        price: parseFloat(priceInput.value),
        category: catInput.value,
        active: true
    };
    
    const resp = await fetch('/api/products/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    
    if (resp.ok) {
        form.reset();
        prependProductRow(payload); // Add to table without reload
        showToast('Product added');
    }
}
```

### Pattern 5: Backend — Handle Partial Field Update

**What:** The existing `/api/products/update` endpoint rewrites the entire row with 7 fields. For inline cell edits, only one field changes at a time. Backend must merge the update with existing row data.

**Critical:** Fetch existing record before updating, merge changed field, then write back.

```python
@app.route('/api/products/update', methods=['POST'])
@login_required
def update_product():
    data = request.get_json()
    product_id = data.get('id', '').strip()
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
    
    products_sheet = db.worksheet('Products')
    records = products_sheet.get_all_records()
    
    # Find existing row
    product_row = None
    existing = {}
    for idx, record in enumerate(records, start=2):
        if record.get('ID') == product_id:
            product_row = idx
            existing = record
            break
    
    # Merge: only update fields present in request
    name = data.get('name', existing.get('Name', ''))
    category = data.get('category', existing.get('Category', ''))
    price = float(data.get('price', existing.get('Price', 0)))
    image_url = data.get('image_url', existing.get('ImageURL', ''))
    active_val = data.get('active', str(existing.get('Active', 'TRUE')).upper() == 'TRUE')
    date_added = existing.get('DateAdded', get_philippines_time().strftime('%Y-%m-%d'))
    
    row_data = [product_id, name, category, price, image_url,
                'TRUE' if active_val else 'FALSE', date_added]
    
    if product_row:
        products_sheet.update(f'A{product_row}:G{product_row}', [row_data])
        return jsonify({'success': True, 'message': 'Product updated'})
    else:
        # New product
        row_data[6] = get_philippines_time().strftime('%Y-%m-%d')
        products_sheet.append_row(row_data)
        return jsonify({'success': True, 'message': 'Product created'})
```

### Pattern 6: Google Sheets Products Sheet Schema

The schema already exists in the codebase (read by `get_products_list`):

```
Column A: ID          (e.g. "PROD-001")
Column B: Name        (e.g. "Chicken Sandwich")
Column C: Category    (e.g. "Food")
Column D: Price       (e.g. 45.00)
Column E: ImageURL    (optional, can be empty)
Column F: Active      ("TRUE" or "FALSE")
Column G: DateAdded   (e.g. "2026-02-26")
```

**Row 1 MUST be headers.** `gspread.get_all_records()` uses row 1 as column names. If the Products sheet doesn't exist yet or has wrong headers, the `/api/products/list` call will return an empty list or 500.

**Verification step:** The plan must include a task that confirms the Products sheet exists with correct headers, or creates it if missing.

### Anti-Patterns to Avoid

- **Don't rewrite cashier_routes.py `complete-sale`** — it already has retry+rollback logic that satisfies PROD-06. Only UI wiring changes needed.
- **Don't add a separate `/api/products/add` endpoint** — the existing `/api/products/update` already handles upsert (creates if ID not found). Use the same endpoint for add and edit.
- **Don't use `modal` for editing** — the existing `products.html` uses Bootstrap modal; the locked decision requires inline row editing. Delete the modal entirely.
- **Don't call `get_all_records()` on every cell save** — for inline row edits, the existing record data is already in the DOM. Fetch it from the row's data attributes, not a fresh API call.
- **Don't filter active products on the backend for the admin view** — admin must see ALL products (active + inactive). Filtering to active-only belongs only in `/cashier/api/products` response or the cashier frontend.
- **Don't use `alert()` for feedback** — currently in `products.html:199`. Must be replaced with Bootstrap toast.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Toast notification | Custom CSS + setTimeout | `bootstrap.Toast` | Already loaded; handles auto-dismiss, stacking, accessibility |
| Toggle switch | Custom styled checkbox | Bootstrap `form-switch` | One CSS class; consistent with Bootstrap 5.3 already in use |
| Inline validation highlight | Custom JS validation | Bootstrap `is-invalid` CSS class | Add class on submit attempt; removed on input change; zero custom CSS |
| Row gray-out for inactive | Custom CSS color manipulation | Bootstrap `table-secondary` class | One class toggle; already in Bootstrap's table variant set |
| Transaction atomicity | Custom lock/retry logic | **Already implemented** in `cashier_routes.py:291` | Phase 1 built retry+rollback; do not replace |

**Key insight:** The project already uses Bootstrap 5.3 for all admin templates. Every UI affordance needed (toast, toggle, badge, table classes) is already available via CDN. No new CSS framework or library is needed.

---

## Common Pitfalls

### Pitfall 1: Products Sheet Does Not Exist in Google Sheets
**What goes wrong:** `/api/products/list` throws `WorksheetNotFound` → 503 response → admin page shows spinner forever.
**Why it happens:** The Products sheet is referenced in code but may not have been manually created in the Google Sheets document.
**How to avoid:** Plan Wave 0 must include a "verify/create Products sheet" task. Use `gspread`'s `add_worksheet` if sheet is missing.
**Warning signs:** 503 on `/api/products/list` in the first test run.

### Pitfall 2: `get_all_records()` Returns Empty on Wrong Headers
**What goes wrong:** Products sheet exists but row 1 has wrong column names (e.g., "id" vs "ID") → `get_all_records()` returns empty dicts with wrong keys → products list is empty or throws KeyErrors.
**Why it happens:** `gspread.get_all_records()` uses the first row as keys exactly as written. Case matters.
**How to avoid:** The plan must specify exact header row values: `ID, Name, Category, Price, ImageURL, Active, DateAdded`. Verify headers match exactly.
**Warning signs:** `record.get('ID', '')` returns empty string for all records.

### Pitfall 3: Inline Edit Fires Multiple `blur` Events
**What goes wrong:** User clicks a cell, types, presses Tab to next cell → `blur` fires on first cell AND focus fires `click` on next cell simultaneously → two API calls fire, second may overwrite with stale data.
**Why it happens:** Browser fires `blur` before `focus` on the new element, but the two events can overlap in async code.
**How to avoid:** Debounce the save function (100ms), or track a `saving` flag to prevent concurrent saves to the same row.

### Pitfall 4: Category Mismatch Between Admin and POS
**What goes wrong:** Admin adds product with category "Snacks" but POS filter tab doesn't show "Snacks" tab because old products in Sheets still have "Stationery" category → cashier sees mixed tabs.
**Why it happens:** Existing `products.json` and potentially existing Sheet rows use old categories (Stationery, Others).
**How to avoid:** Plan must update category dropdown options in both `products.html` and `cashier_index.html` to the locked list: Food, Drinks, Snacks, Other. Also update `products.json` (sample data) for consistency.

### Pitfall 5: Cashier Checkout Requires Arduino to Be Connected
**What goes wrong:** Cashier sees products, builds cart, clicks "Pay Now" → `checkout()` in `cashier_index.html:301` checks `arduinoConnected` and blocks with `alert('Arduino not connected!')` → cashier cannot complete a transaction without hardware.
**Why it happens:** The existing `checkout()` function in `cashier_index.html` has a hard guard: `if (!arduinoConnected) { alert(...); return; }`.
**How to avoid:** For Phase 3 the requirement is that the cashier CAN process a transaction (PROD-06). The Arduino/card-tap flow is the target path. This guard is correct behavior — document it as a known UX dependency, not a bug to fix. Verification of PROD-06 requires Arduino hardware OR a test that bypasses the hardware path via WebSocket event injection.

### Pitfall 6: `db` Module-Level Global Fails on Sheets Reconnect
**What goes wrong:** `admin_dashboard.py:130` initializes `db = get_sheets_client()` at module load. If the Sheets connection drops and `db` becomes stale, calls like `db.worksheet('Products')` fail without triggering reconnect logic.
**Why it happens:** The global `db` is initialized once; `get_worksheet_with_retry` refreshes it on retry but direct `db.worksheet()` calls in product endpoints do NOT use `get_worksheet_with_retry`.
**How to avoid:** The three product endpoints (`get_products_list`, `update_product`, `delete_product`) call `db.worksheet('Products')` directly. Change these to use `get_worksheet_with_retry('Products')` for consistency with the rest of the file.

---

## Code Examples

### gspread: Get All Records from Products Sheet
```python
# Source: existing pattern in admin_dashboard.py:302
products_sheet = get_worksheet_with_retry('Products')
records = products_sheet.get_all_records()
# Returns: [{'ID': 'PROD-001', 'Name': 'Chicken Sandwich', ...}, ...]
```

### gspread: Update a Single Row (Batch)
```python
# Source: existing pattern in admin_dashboard.py:366
products_sheet.update(f'A{product_row}:G{product_row}', [row_data])
# row_data is a list: [id, name, category, price, image_url, 'TRUE'/'FALSE', date_added]
```

### gspread: Toggle Active Column Only
```python
# Source: existing pattern in admin_dashboard.py:397
products_sheet.update_cell(product_row, 6, 'TRUE' if active else 'FALSE')
# Column 6 = F = Active
```

### gspread: Create Products Sheet If Missing
```python
try:
    sheet = db.worksheet('Products')
except gspread.exceptions.WorksheetNotFound:
    sheet = db.add_worksheet(title='Products', rows=100, cols=7)
    sheet.update('A1:G1', [['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded']])
```

### Bootstrap 5.3: Toggle Switch in Table Row
```html
<!-- Source: Bootstrap 5.3 docs — form-switch component -->
<div class="form-check form-switch mb-0">
    <input class="form-check-input" type="checkbox" role="switch" 
           id="active-PROD-001" checked
           onchange="toggleStatus('PROD-001', this.checked)">
</div>
```

### Bootstrap 5.3: Toast Notification
```javascript
// Source: Bootstrap 5.3 docs — Toast component
const toastEl = document.getElementById('saveToast');
const toast = new bootstrap.Toast(toastEl, { delay: 2000, autohide: true });
toast.show();
```

---

## State of the Art

| Old Approach (Current) | Required Approach | Impact |
|------------------------|-------------------|--------|
| Card grid with Bootstrap modal for edit | HTML table with inline row editing | Full products.html rewrite required |
| `alert()` for save feedback | Bootstrap Toast | Minor JS change |
| Deactivate via modal form | Toggle switch in table row | UI pattern change |
| Hard-coded category list includes Stationery/Others | Fixed list: Food, Drinks, Snacks, Other | Update both templates + sample data |
| Direct `db.worksheet()` in product routes | `get_worksheet_with_retry()` | Resilience improvement |
| Product ID entered manually by admin | Auto-generated `PROD-{timestamp}` in JS | Remove ID field from add form |

**Deprecated/outdated in this context:**
- `products.html` modal pattern: Must be replaced entirely; do not extend it.
- `products.json` sample data: Categories (Stationery/Others) are stale vs locked decisions.

---

## Open Questions

1. **Does the Products sheet already exist in Google Sheets?**
   - What we know: The code references it but test_phase3.py's `test_products_management()` calls the live endpoint; we cannot tell from code alone if the sheet was created.
   - What's unclear: Whether any data is in the sheet currently.
   - Recommendation: Wave 0 task must include a "verify Products sheet exists with correct headers" step; create it if missing.

2. **Does the cashier's `complete-sale` endpoint correctly handle multi-item transactions from the new product IDs?**
   - What we know: `complete-sale` stores `items` as `json.dumps(items)` in the transaction log, and `total` as the sum. The items list format is `[{name, price, qty}]` — product ID is not stored in the transaction.
   - What's unclear: Phase 4 (student itemized receipt) will need item-level detail. PROD-06 only requires the transaction completes; Phase 4 concern is deferred.
   - Recommendation: Do not change transaction log format in Phase 3. Document the schema gap as a known issue for Phase 4.

3. **Is the "Add Product" form ID field user-entered or auto-generated?**
   - What we know: The locked decision says form is always visible (name, price, category). ID is not mentioned in the decision.
   - What's unclear: Should admin enter a product ID, or is it auto-generated?
   - Recommendation: Auto-generate `PROD-{Date.now()}` client-side. This removes a friction point (user doesn't need to invent IDs) and prevents collision. Hidden field in form, not visible to admin.

---

## Sources

### Primary (HIGH confidence)
- Codebase read: `backend/dashboard/admin_dashboard.py` — all existing product API endpoints, gspread patterns, error handling conventions
- Codebase read: `backend/dashboard/cashier/cashier_routes.py` — complete-sale transaction flow, JWT auth pattern
- Codebase read: `backend/dashboard/templates/products.html` — current admin UI; confirmed modal pattern that must be replaced
- Codebase read: `backend/dashboard/cashier/templates/cashier_index.html` — current POS UI; confirmed category filter tabs and cart sidebar
- Codebase read: `backend/data/products.json` — confirmed existing sample data with wrong category names
- Codebase read: `tests/conftest.py` — test fixture patterns; confirmed mock_google_sheets does not include Products sheet mock

### Secondary (MEDIUM confidence)
- Bootstrap 5.3 documentation patterns (training knowledge, consistent with CDN link already in templates)
- gspread API patterns: `get_all_records`, `update`, `update_cell`, `append_row`, `add_worksheet` — confirmed in existing codebase usage

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use; no new dependencies
- Architecture: HIGH — existing code read directly; gaps are confirmed observations not assumptions
- Pitfalls: HIGH (Pitfalls 1-4) / MEDIUM (Pitfall 5-6) — 1-4 from direct code observation; 5-6 from code pattern analysis

**Research date:** 2026-02-26
**Valid until:** 2026-03-28 (stable stack; gspread API rarely changes)
