# Plan 20-01 Summary: M3 Theme Migration + Inter Font

## Status: COMPLETE ✅

## What Was Done

### Task 1: Replace colors.xml with full M3 role palette
- Replaced all placeholder colors (`purple_*`, `teal_*`) with a complete M3 color role palette derived from seed `#0057A8`
- All light (`md_theme_light_*`) and dark (`md_theme_dark_*`) roles defined
- Build verified: `BUILD SUCCESSFUL`

### Task 2: Upgrade themes.xml to M3 + wire Inter font + color roles
- Downloaded Inter v4.0 TTFs from GitHub release (`rsms/inter`)
- Created `res/font/inter_regular.ttf`, `inter_medium.ttf`, `inter_semibold.ttf`
- Created `res/font/inter.xml` font family descriptor (weights 400/500/600)
- Created `res/values/type.xml` with 14 `TextAppearance.App.*` styles (all override `fontFamily` to `@font/inter`)
- Rewrote `themes.xml`: parent is `Theme.Material3.DayNight.NoActionBar`, all M3 color role attributes wired

## Deviations from Plan

- **Theme name**: Plan specified `Theme.StudentApp` but `AndroidManifest.xml` uses `Theme.BankoNgSetonAndroid`. Used `Theme.BankoNgSetonAndroid` throughout.
- **Attribute name corrections** (Material 1.11.0 vs plan's M3 attr names):
  - Removed `colorSurfaceTint` (attribute does not exist in Material 1.11.0)
  - Renamed `colorInverseSurface` → `colorSurfaceInverse`
  - Renamed `colorInverseOnSurface` → `colorOnSurfaceInverse`
  - Renamed `colorInversePrimary` → `colorPrimaryInverse`
- **Gradle wrapper**: `gradle-wrapper.jar` is corrupted (no main manifest). Used system Gradle 8.5 extracted to `/tmp/gradle-extract/gradle-8.5/` with `JAVA_HOME` set to Android Studio JBR.

## Verification

```
BUILD SUCCESSFUL in 15s
36 actionable tasks: 11 executed, 25 up-to-date
```

Only pre-existing deprecation warnings (`startActivityForResult`, `FLAG_FULLSCREEN`) — not from our changes.

## Files Modified

| File | Action |
|------|--------|
| `res/values/colors.xml` | Replaced with full M3 palette |
| `res/values/themes.xml` | Replaced with M3 theme (corrected attr names) |
| `res/values/type.xml` | Created — 14 TextAppearance.App.* overrides |
| `res/font/inter_regular.ttf` | Created — Inter weight 400 |
| `res/font/inter_medium.ttf` | Created — Inter weight 500 |
| `res/font/inter_semibold.ttf` | Created — Inter weight 600 |
| `res/font/inter.xml` | Created — font family descriptor |
