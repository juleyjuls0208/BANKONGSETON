# WSGI Configuration for PythonAnywhere
# This file configures the web app for PythonAnywhere hosting

import sys
import os

# Add your project directory to the path
project_home = '/home/bankoseton/FinanceDashboard'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set non-secret config defaults only.
# All secrets (SECRET_KEY, FLASK_SECRET_KEY, credentials, API keys) MUST be set via
# the .env file or PythonAnywhere environment variables dashboard — never hardcoded here.
os.environ['GOOGLE_SHEETS_ID'] = '1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0'
os.environ['GOOGLE_CREDENTIALS_FILE'] = 'credentials.json'

# Import the Flask app (WEB-ONLY version without Arduino)
from web_app import app as application
