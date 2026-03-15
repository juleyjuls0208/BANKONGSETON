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

# Non-secret config defaults (safe to set here)
os.environ.setdefault('GOOGLE_SHEETS_ID', '1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0')
os.environ.setdefault('GOOGLE_CREDENTIALS_FILE', 'credentials.json')

# Import the Flask app (web-only version, no Arduino/serial dependencies)
from web_app import app as application
