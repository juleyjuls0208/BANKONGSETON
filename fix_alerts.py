import re

file_path = "backend/dashboard/templates/fraud_alerts.html"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the dummy filters search if we can
# Is there a dummy alert for loadAlerts? Let's add loadAlerts if it doesn't exist
if "function loadAlerts(" not in content:
    print("loadAlerts not found, checking if it is already there")
