# WSGI Configuration for PythonAnywhere
# This file configures the web app for PythonAnywhere hosting

import sys
import os

# Add your project directory to the path
project_home = '/home/bankoseton/FinanceDashboard'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables (optional - better to use .env file)
# These are just defaults, .env file will override them
os.environ['GOOGLE_SHEETS_ID'] = '1S8GHhRCb8rztEAJK2XhPD7t6Oy_UL2fiNrOVgUPQ_P0'
os.environ['SECRET_KEY'] = 'bangko-admin-secret-key-change-in-production'
os.environ['FLASK_SECRET_KEY'] = 'bangko-admin-secret-key-change-in-production'
os.environ['FINANCE_USERNAME'] = 'financedashboard'
os.environ['FINANCE_PASSWORD'] = 'finance2025'
os.environ['ADMIN_USERNAME'] = 'admindashboard'
os.environ['ADMIN_PASSWORD'] = 'admin2025'
os.environ['ARDUINO_API_KEY'] = 'bangko-arduino-bridge-secure-key-2026'
os.environ['GOOGLE_CREDENTIALS_FILE'] = 'credentials.json'

# Import the Flask app (WEB-ONLY version without Arduino)
from web_app import app as application
