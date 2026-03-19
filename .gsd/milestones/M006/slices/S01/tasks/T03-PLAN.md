# T03: Create POS UI skeleton and login templates

## Description
Provide the actual user interface for the cashier to interact with. This task creates the HTML templates for the login page and the main POS skeleton, and wires them to the backend routes. It ensures the full authentication flow works end-to-end in the browser.

## Steps
1. Create directories `backend/cashier_app/templates/` and `backend/cashier_app/static/` (if needed for CSS/JS).
2. Create `backend/cashier_app/templates/login.html`. Build a clean, modern login form (username, password, submit button). Add minimal inline or external CSS.
3. Write JavaScript in `login.html` to intercept the form submission, send a `POST` to `/api/login`, and on success, redirect to `/`. On failure, display an error message.
4. Create `backend/cashier_app/templates/pos.html`. Build a skeleton layout representing the future POS (header, sidebar placeholder, main content area, order panel placeholder).
5. In `app.py` or a new `routes/ui.py` (registered in app.py), add:
   - `GET /login` which renders `login.html`.
   - `GET /` which is decorated with `@jwt_required` and renders `pos.html`.
6. Ensure the `jwt_required` decorator redirects to `/login` if the user accesses `/` without a valid token.

## Must-Haves
- `login.html` with a functional fetch-based form submission.
- `pos.html` skeleton layout.
- `GET /login` route.
- `GET /` route protected by JWT.
- Unauthorized access to `/` must redirect to `/login`.

## Verification
- Start the server on port 5010.
- Open `http://localhost:5010/` in a browser. It should redirect to `/login`.
- Enter valid cashier credentials and submit.
- It should successfully log in and redirect to `http://localhost:5010/`, displaying the POS skeleton.

## Inputs
- `backend/cashier_app/app.py`
- `backend/cashier_app/routes/auth.py`

## Expected Output
- Renderable `login.html` and `pos.html`.
- Working frontend login flow connecting UI to the API.
- Protected root route serving the POS application.
## Observability Impact
- Runtime signals: Access logs for `/login` and `/` endpoints, JWT validation failures in Flask logs.
- Inspection surfaces: Browser DevTools (Network tab for API calls, Console for JS errors in UI flows).
- Failure visibility: UI display of login failure messages, network failures or unexpected redirects observable in browser network logs.
