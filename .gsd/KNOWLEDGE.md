# GSD Knowledge

Project-level knowledge base — non-obvious rules, recurring gotchas, and useful patterns discovered during execution.

---

## Android: Removing a layout view ID requires removing its corresponding `lateinit var` binding

**Context:** When replacing `activateNfcPayButton` (hidden NFC button) with `qrPayButton` in `activity_home.xml`, the plan said to leave NFC dead code intact. However, `activateNfcPayButton = findViewById(R.id.activateNfcPayButton)` and its click listener must still be removed even when leaving the field declaration — because `findViewById` on a non-existent layout ID returns `null`, and calling any method on the resulting `lateinit var` causes an NPE at runtime.

**Rule:** When a layout XML view is removed, always remove:
1. The `= findViewById(R.id.viewId)` binding call
2. Any click listeners or method calls on that view in lifecycle methods

The `private lateinit var` field declaration and any dead function bodies referencing it can stay for later cleanup.

---

## Android CameraX: ExperimentalGetImage opt-in required on processImage

The `imageProxy.image` accessor is annotated `@ExperimentalGetImage` in CameraX 1.3.x. Functions calling it must be annotated with `@androidx.annotation.OptIn(androidx.camera.core.ExperimentalGetImage::class)`. Without this, the build will fail with an error about using experimental API.

---

## ML Kit barcode scanning: scanning flag prevents double-scan race

When using ML Kit in an `ImageAnalysis.Analyzer`, frames arrive on the camera executor thread while the UI runs on the main thread. Set `scanning = false` **synchronously on the camera thread** before calling `runOnUiThread { fetchCart(token) }` — not inside the `runOnUiThread` block. This prevents two back-to-back frames both seeing the same QR code and triggering two `fetchCart` calls.

---

## RTK command passthrough: use `rtk proxy` for raw commands like Python/pytest

In this repo workflow, `rtk <command>` does not accept every arbitrary executable directly (e.g., `rtk python ...` errors with “unrecognized subcommand”). For non-native RTK wrappers, use:

- `rtk proxy python ...`
- `rtk proxy python -m pytest ...`
- `rtk proxy curl ...`

This keeps the “always prefix with RTK” rule while still running passthrough commands successfully.

---

## Browser verification fallback: use `performance.getEntriesByType('resource')` when network log buffer is empty

In this environment, `browser_get_network_logs` may occasionally return no entries even when the page performed fetches. For slice verification that needs request-path evidence, use:

```js
performance.getEntriesByType('resource').map(e => e.name)
```

Then assert expected paths (e.g., `/api/products`) and absence of forbidden ports (e.g., `:5003`) via `browser_evaluate`.

---

## POS auth fetch handling: check both HTTP 401 and redirected `/login`

In the standalone cashier app, unauthenticated API requests may be surfaced either as:
- an explicit `401` response, or
- a fetch response with `response.redirected === true` and `response.url` ending in `/login`.

When bootstrapping POS data (`/api/products`), treat **both** as unauthenticated and force `window.location.href = '/login'`.

This keeps frontend auth handling stable even if backend auth behavior toggles between direct status codes and redirect-based middleware.

---

## POS cart rendering: use DOM APIs (not `innerHTML`) for Sheets-driven item names

When rendering cart rows from `/api/products`, treat product fields as untrusted because canteen staff can edit the source Google Sheet directly. Build rows with `document.createElement(...)` and assign user-visible content via `textContent`.

This keeps quantity controls safe/explicit (`data-cart-action`, `data-product-key`) and avoids accidental markup/script injection from product names or categories.

---

## Standalone POS UAT without hardware: trigger SocketIO handlers via cached callbacks

When hardware/student flows are unavailable during browser UAT, standalone POS SocketIO handlers can be exercised by invoking callback arrays on `window.cashierSocket._callbacks` directly in `browser_evaluate`.

Examples:
- RFID path trigger: `(window.cashierSocket._callbacks.$card_read||[]).forEach(fn => fn({success:true, uid:'5F6E7D8C'}))`
- QR completion trigger: `(window.cashierSocket._callbacks.$qr_payment||[]).forEach(fn => fn({success:true, new_balance:500}))`
- WiFi status trigger: `(window.cashierSocket._callbacks.$arduino_wifi_status||[]).forEach(fn => fn({online:true, state:'online', last_seen_s:0}))`

This is useful for validating POS state transitions deterministically while still verifying real route wiring and endpoint traffic on port 5010.

---

## QR confirm safety: emit `qr_payment` before clearing `pending_qr_token`

In standalone QR confirmation (`/api/qr/confirm`), keep the ordering:
1. `socketio.emit('qr_payment', ...)`
2. then clear `current_app.pending_qr_token`

If token clear happens first, the Arduino poller can read null immediately and drop the QR before cashier UI receives the completion event, producing flaky “QR disappeared but no success state” behavior.

Lock this with route-contract tests by asserting token is still present at emit time.

---

## Python 3.14 + importlib: register dynamically loaded module in `sys.modules` before executing dataclass code

When loading a script module from a file path in tests via `importlib.util.module_from_spec`, insert it into `sys.modules` before `spec.loader.exec_module(module)`.

Without that registration, Python 3.14 dataclass processing can fail with:
`AttributeError: 'NoneType' object has no attribute '__dict__'`

Pattern:

```python
spec = importlib.util.spec_from_file_location("module_name", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
```

---

## Windows shell constraint: `rtk proxy bash ...` fails when `/bin/bash` is unavailable

In this harness, `rtk proxy bash ...` invokes `/bin/bash` through WSL. On hosts where WSL/bash is not installed, commands fail with:
`execvpe(/bin/bash) failed: No such file or directory`.

When this happens:
1. Keep committed `.sh` wrappers as the canonical verifier entrypoints for Linux/CI parity.
2. Run equivalent Python verification commands directly (`rtk proxy python ...`) so evidence artifacts can still be generated in Windows-only environments.
3. Document the shell constraint explicitly in task verification evidence so future agents do not misclassify it as a code regression.

---

## Verification ordering: do not run dependent bundle assertions in parallel with bundle generation

For S05 evidence checks, running the JSON assertion command in parallel with `verify-m006-s05-bundle.py` can intermittently fail with `FileNotFoundError` because the bundle file is read before it is written.

Run in this order instead:
1. Generate bundle (`verify-m006-s05-bundle.py`)
2. Then run assertion command against `S05-UAT-BUNDLE.json`

This avoids false negatives caused by command ordering rather than actual verification failures.

---

## S04 verifier side effect: preflight failures still overwrite `S04-LIVE-PROOF.json`

`rtk proxy python scripts/verify-m006-s04-live.py ...` writes the evidence file even when preflight fails (`missing_env`/`missing_inputs`). That means a previously passing `S04-LIVE-PROOF.json` can be replaced by a failing artifact, which then cascades into S05 bundle regressions.

Safe pattern when running docs/traceability work:
1. Run S04 verifier only when required env/runtime inputs are present.
2. If preflight fails but you need to preserve closure docs, regenerate/restore the intended S04 evidence before rerunning `verify-m006-s05-bundle.py`.
3. Re-assert `S05-UAT-BUNDLE.json` (`overall.live_ready`, required flow classifications, no `:5003`) after restoration.

---

## Milestone closeout guardrail: placeholder slice summaries are non-authoritative

Auto-mode recovery can leave a slice summary as a `BLOCKER` placeholder even when downstream verifier artifacts are later restored to pass-state.

**Rule:** for closure decisions, treat machine evidence artifacts as source-of-truth before prose placeholders:
1. Verify gate artifacts first (`S04-LIVE-PROOF.json`, `S05-UAT-BUNDLE.json`).
2. Confirm required flow classifications (`live_success`) and topology checks (no forbidden ports).
3. Then publish milestone summary/traceability docs; do not infer failure from placeholder prose alone.

This prevents false milestone regressions caused by artifact-generation order and recovery placeholders rather than real runtime breakage.
