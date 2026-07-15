---
version: alpha
name: BankongSeton — Premium
description: Apple-style premium design system for the BankongSeton cashless canteen landing page. Deep ink, frosted glass, a single warm gold accent, generous whitespace, and fluid motion.
colors:
  primary: "#0B0B0F"
  secondary: "#6E6E73"
  tertiary: "#C8A24B"
  neutral: "#F5F5F7"
  accent: "#0A84FF"
  surface: "#FFFFFF"
  inkSoft: "#1D1D1F"
  line: "#E3E3E8"
  success: "#30D158"
  danger: "#FF453A"
typography:
  h1:
    fontFamily: "SF Pro Display, -apple-system, BlinkMacSystemFont, Inter, sans-serif"
    fontSize: "5.5rem"
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  h2:
    fontFamily: "SF Pro Display, -apple-system, BlinkMacSystemFont, Inter, sans-serif"
    fontSize: "3.25rem"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  h3:
    fontFamily: "SF Pro Display, -apple-system, BlinkMacSystemFont, Inter, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  body-lg:
    fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, Inter, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "0"
  body-md:
    fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, Inter, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "0"
  eyebrow:
    fontFamily: "SF Pro Text, -apple-system, BlinkMacSystemFont, Inter, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.12em"
rounded:
  sm: 10px
  md: 18px
  lg: 28px
  xl: 40px
  pill: 999px
spacing:
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  xxl: 120px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.primary}"
    rounded: "{rounded.pill}"
    padding: 16px
    typography: "{typography.body-md}"
  button-primary-hover:
    backgroundColor: "{colors.neutral}"
  button-secondary:
    backgroundColor: "rgba(255,255,255,0.08)"
    textColor: "{colors.surface}"
    rounded: "{rounded.pill}"
    padding: 16px
    typography: "{typography.body-md}"
  button-secondary-hover:
    backgroundColor: "rgba(255,255,255,0.16)"
  surface-glass:
    backgroundColor: "rgba(245,245,247,0.6)"
    rounded: "{rounded.lg}"
  card-premium:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.xl}"
    padding: 40px
  text-eyebrow:
    textColor: "{colors.tertiary}"
    typography: "{typography.eyebrow}"
---

## Overview

BankongSeton — "Bangko ng Seton" — is the cashless canteen system for Elizabeth Seton
School. The brand should feel premium, calm, and trustworthy: the kind of
restraint you see in great product pages. A near-black canvas, frosted glass,
and one warm gold accent (the "peso" hue) carry the whole identity. Motion is
fluid and purposeful — it guides the eye, it never shouts.

## Colors

- **Primary (#0B0B0F):** Deep near-black. The page canvas and the ink for
  headlines on light surfaces.
- **Secondary (#6E6E73):** Apple-gray for body copy and captions.
- **Tertiary (#C8A24B):** "Seton Gold" — the single high-emphasis accent.
  Represents the peso balance. Used sparingly: one CTA, one underline, the
  active state.
- **Neutral (#F5F5F7):** Apple light background for the lower sections.
- **Accent (#0A84FF):** iOS system blue, reserved for links and interactive
  affordances that are not the primary buy-in action.
- **Surface (#FFFFFF):** Cards and the glass layer base.
- **Success (#30D158) / Danger (#FF453A):** iOS semantic colors for the
  "balance" and "alert" states in product UI mockups.

## Typography

SF Pro first, with Inter as the webfont fallback so the page renders identically
off-Apple hardware. One display scale for the hero, a tight tracking scale for
section heads, and a relaxed body scale for reading. Eyebrows are uppercase,
gold, and letter-spaced — the only all-caps treatment on the page.

## Layout

Generous vertical rhythm: 120px between major sections on desktop, scaling down
on mobile. Content is centered with a max width of 1120px. The hero is
full-bleed with a fixed Three.js canvas behind it. Lower sections alternate
light/dark to create a "scrolling through product reveal" cadence.

## Elevation & Depth

Depth comes from frosted glass (backdrop-blur) and soft, low-opacity shadows —
never hard borders. Cards float on a subtle 0 20px 60px rgba(0,0,0,0.08) glow.
The gold accent carries a faint 0 8px 30px rgba(200,162,75,0.35) bloom when
active.

## Shapes

Radii are large and friendly: 28px on cards, full pills on buttons. Nothing
sharp. The product mockups use 40px radius to echo a device screen.

## Components

`button-primary` is the only gold action — the "Get the system" CTA. Everything
else is glass or ghost. `surface-glass` is the frosted nav and floating stat
bars. `card-premium` holds feature copy. `text-eyebrow` labels each section.

## Do's and Don'ts

- **Do** keep the palette to ink + one gold + glass. Add color only for live
  product states (green/red balance).
- **Do** let anime.js handle entrance and scroll motion — ease `outExpo`,
  durations 700–1100ms, never linear.
- **Don't** use more than one gold element competing for attention per
  viewport.
- **Don't** animate layout properties (width/height/margin) — transform and
  opacity only, for 60fps on the canvas.
