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
