import re

file_path = "backend/dashboard/templates/cashier_accounts.html"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

toggle_script = """
    document.getElementById('toggleNewPassword').addEventListener('click', function() {
        const pwd = document.getElementById('newPassword');
        const icon = this.querySelector('i');
        if (pwd.type === 'password') {
            pwd.type = 'text';
            icon.classList.replace('bi-eye', 'bi-eye-slash');
        } else {
            pwd.type = 'password';
            icon.classList.replace('bi-eye-slash', 'bi-eye');
        }
    });

    document.getElementById('toggleConfirmPassword').addEventListener('click', function() {
        const pwd = document.getElementById('confirmPassword');
        const icon = this.querySelector('i');
        if (pwd.type === 'password') {
            pwd.type = 'text';
            icon.classList.replace('bi-eye', 'bi-eye-slash');
        } else {
            pwd.type = 'password';
            icon.classList.replace('bi-eye-slash', 'bi-eye');
        }
    });
"""

if "toggleNewPassword" in content and "addEventListener" not in content.split("toggleNewPassword")[1]:
    content = content.replace("document.addEventListener('DOMContentLoaded', loadAccounts);", "document.addEventListener('DOMContentLoaded', () => {\n        loadAccounts();" + toggle_script + "\n    });")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added password toggle logic to cashier_accounts.html")
else:
    print("Toggle already handled or issue")
