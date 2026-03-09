---
created: 2026-03-09T11:13:00.513Z
title: Remove pin in iOS app
area: auth
files: []
---

## Problem

The iOS app has a PIN feature that needs to be removed. This may refer to a PIN code entry/authentication screen or SSL certificate pinning in the iOS network layer.

## Solution

TBD — identify the specific pin implementation to remove:
1. Locate PIN-related code in the iOS app (authentication screens, security settings)
2. Remove PIN entry UI and associated logic
3. If SSL/certificate pinning — remove from network layer and verify API calls succeed
4. Test login and authenticated flows after removal
