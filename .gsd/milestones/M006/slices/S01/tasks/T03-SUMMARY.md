---
title: "Create POS UI skeleton and login templates"
observability_surfaces:
  - client side console logs
  - network panel requests
---

# T03: Create POS UI skeleton and login templates

Implemented the HTML templates and routing for the standalone cashier POS app. The work introduces `login.html` with a Javascript-based login form submitting to the `/api/login` backend, and `pos.html` as the main skeleton view for the POS functionality (categories, items, order panel). 

The routes were registered into a new `ui_bp` Blueprint that intercepts root (`/`) requests. It uses a custom decorator `@jwt_cookie_required` to check the `cashier_token` HttpOnly cookie set by the authentication route and automatically redirects unauthenticated requests to the `/login` route. 

All verification steps passed successfully, proving the standalone cashier app handles UI routing, login, cookie setting, and redirection properly.

## Verification Evidence
| Command / Action | Output / Result | Status |
| --- | --- | --- |
| `python backend/cashier_app/app.py` | Server starts on port 5010 | ✅ |
| Access root (`/`) without token | Redirects to `/login` | ✅ |
| Submit valid credentials | Logs in, redirects to `/`, shows POS UI | ✅ |

## Diagnostics
- Frontend errors in `login.html` and `pos.html` can be viewed in browser console logs.
- Login API requests and responses can be inspected in browser network dev tools.

