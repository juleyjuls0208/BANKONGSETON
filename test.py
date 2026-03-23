import re

html_files = [
    "backend/dashboard/templates/dashboard.html",
    "backend/dashboard/templates/students.html",
    "backend/dashboard/templates/transactions.html",
    "backend/dashboard/templates/products.html",
    "backend/dashboard/templates/cashier_accounts.html",
    "backend/dashboard/templates/fraud_alerts.html",
    "backend/dashboard/templates/parent_dashboard.html",
    "backend/cashier_app/templates/cashier_index_standalone.html"
]

for file in html_files:
    try:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
            # find buttons that don't have onclick, don't have type="submit", and don't have data-bs-toggle
            buttons = re.findall(r'<button[^>]*>.*?</button>', content, re.IGNORECASE | re.DOTALL)
            suspicious = []
            for b in buttons:
                if 'onclick' not in b.lower() and 'type="submit"' not in b.lower() and 'data-bs-toggle' not in b.lower() and 'data-bs-dismiss' not in b.lower():
                    # check if they have id and are bound in JS
                    id_match = re.search(r'id=["\']([^"\']+)["\']', b, re.IGNORECASE)
                    if id_match:
                        id_val = id_match.group(1)
                        if id_val in content:
                            pass # likely bound
                        else:
                            suspicious.append(b)
                    else:
                        suspicious.append(b)
            if suspicious:
                print(f"--- {file} ---")
                for s in suspicious:
                    clean_s = re.sub(r'\s+', ' ', s)
                    print(clean_s[:100] + "..." if len(clean_s) > 100 else clean_s)
    except Exception as e:
        pass
