---
created: 2026-03-09T11:11:46.842Z
title: Fix iOS login network error
area: auth
files: []
---

## Problem

When logging in on iOS, users see the error: "Network error. Check your connection and try again."

The login request is failing on iOS specifically. This may be related to SSL/TLS certificate pinning, ATS (App Transport Security) configuration, incorrect API base URL for the iOS build, missing network permissions, or a platform-specific HTTP client issue.

## Solution

TBD — investigate the iOS network layer during login:
1. Check API base URL config for iOS builds
2. Verify ATS settings in Info.plist allow the backend domain
3. Check if the error originates from a failed fetch/axios call and capture the underlying error code
4. Test on a real device vs simulator to isolate environment issues
