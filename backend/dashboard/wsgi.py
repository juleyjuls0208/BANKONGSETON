# WSGI Configuration for PythonAnywhere
# This file is the entry point for PythonAnywhere WSGI hosting.
#
# ── Deployment Checklist ────────────────────────────────────────────────────
# 1. Upload credentials.json to:
#    /home/bankoseton/BANKONGSETON/backend/dashboard/config/credentials.json
# 2. Create /home/bankoseton/BANKONGSETON/.env with the following variables:
#
#    Required:
#      FLASK_SECRET_KEY=<random 32+ char string>
#        Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
#      JWT_SECRET=<random 32+ char string>
#        Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"
#      GOOGLE_CREDENTIALS_FILE=/home/bankoseton/BANKONGSETON/backend/dashboard/config/credentials.json
#      GOOGLE_SHEETS_ID=1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0
#
#    Optional (email notifications):
#      SMTP_HOST=smtp.gmail.com
#      SMTP_PORT=587
#      SMTP_USER=your@email.com
#      SMTP_PASSWORD=your_app_password
#      SMTP_FROM=your@email.com
#
#    Optional (admin credentials — if not set, admin login is disabled):
#      ADMIN_USERNAME=admin
#      ADMIN_PASSWORD=<strong password>
#      FINANCE_USERNAME=financedashboard
#      FINANCE_PASSWORD=<strong password>
# ────────────────────────────────────────────────────────────────────────────

import sys
import os

# Project directory (PythonAnywhere path)
project_home = '/home/bankoseton/BANKONGSETON/backend/dashboard'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load secrets from .env BEFORE importing the app.
# web_app.py has startup guards that run at import time — dotenv must load first.
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '..', '..', '.env'))

# Set non-secret config defaults (only if not already set by .env).
# Secrets MUST come from .env — never hardcode them here.
os.environ.setdefault('GOOGLE_SHEETS_ID', '1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0')
# Use absolute path for credentials to avoid CWD-relative resolution issues on PythonAnywhere.
os.environ.setdefault(
    'GOOGLE_CREDENTIALS_FILE',
    os.path.join(project_home, 'config', 'credentials.json')
)

# Import the Flask app (hardware-free version — no Arduino/serial required).
from web_app import app as application
