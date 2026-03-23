# Standalone Cashier App (`:5010`)

This folder now contains the cashier app and its local dependencies so cashier can run without opening the admin dashboard UI.

## Entry point

- `app.py`

## Install

```bash
pip install -r backend/cashier_app/requirements.txt
```

## Run

```bash
python backend/cashier_app/app.py
```

or on Windows:

```bash
run_cashier.bat
```

## Local copied support files

- `cashier_routes.py`
- `templates/cashier_login*.html`
- `templates/cashier_index*.html`
- `cache.py`
- `offline_queue.py`
- `notifications.py`
- `errors.py`
- `services/email_service.py`
- `api/fcm_sender.py`

## Cashier URL

- `http://localhost:5010/login`
