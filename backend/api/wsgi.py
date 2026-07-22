# WSGI entry point for PythonAnywhere — Bangko ng Seton Mobile API
#
# PythonAnywhere setup:
#   Web app source code:  /home/bankoseton/FinanceDashboard
#   WSGI config file:     /home/bankoseton/FinanceDashboard/backend/api/wsgi.py
#   Working directory:    /home/bankoseton/FinanceDashboard/backend/api
#   Virtualenv (optional): /home/bankoseton/.virtualenvs/bankongseton
#
# Required packages (pip install -r backend/api/requirements_api.txt):
#   flask, flask-cors, pyjwt, cryptography,
#   firebase-admin, python-dotenv, pytz, requests, gunicorn
#
# Set these in the PythonAnywhere Web tab → Environment Variables:
#   JWT_SECRET    — stable secret; never let it randomise on restart

import sys
import os

project_home = "/home/juley2823/FinanceDashboard"

# Add all paths api_server.py and its dependencies need
for _p in [
    project_home,  # project root
    os.path.join(
        project_home, "backend"
    ),  # errors, utils, nfc_payments, migrate_transactions
    os.path.join(project_home, "backend", "api"),  # api_server, fcm_sender
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Set env vars BEFORE importing api_server.
# CORS origins are evaluated at module import time — must be set here.
os.environ.setdefault("FLASK_ENV", "production")
os.environ.setdefault("CORS_ORIGINS", "https://juley2823.pythonanywhere.com")

# Activate structured logging.
# Normally called inside __main__; must be called here so WSGI logs are structured.
try:
    from errors import setup_logging

    setup_logging()
except Exception:
    import logging

    logging.basicConfig(level=logging.INFO)

from api_server import app as application  # noqa: E402  (PythonAnywhere requires 'application')
