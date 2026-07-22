# WSGI Configuration for PythonAnywhere
# Replace YOUR_USERNAME with your actual PythonAnywhere username.
#
# On PythonAnywhere: Web tab → click your web app → WSGI configuration file
# Paste this file's content (or point to it), replacing YOUR_USERNAME.

import sys
import os
from dotenv import load_dotenv

# Project root — MUST be the BANKONGSETON directory, not a subdirectory
project_home = '/home/YOUR_USERNAME/BANKONGSETON'

# Add all three levels to sys.path so backend/ and backend/dashboard/ modules resolve
for _p in [
    project_home,
    os.path.join(project_home, 'backend'),
    os.path.join(project_home, 'backend', 'dashboard'),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Load secrets from .env at project root (not committed to git — create it on the server)
# Alternative: set env vars via PythonAnywhere Web tab → Environment variables panel
load_dotenv(os.path.join(project_home, '.env'))

# DATABASE_URL must be provided by the deployment environment; Google Sheets is disabled.
os.environ.pop("GOOGLE_SHEETS_ID", None)
os.environ.pop("GOOGLE_CREDENTIALS_FILE", None)

# Import the Flask app (web-only version, no Arduino/serial dependencies)
from web_app import app as application
