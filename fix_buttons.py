import re

files = {
    "backend/dashboard/templates/students.html": [
        ('<button class="action-btn secondary"><i class="bi bi-funnel me-1"></i>Filter</button>', '<button class="action-btn secondary" onclick="alert(\'Filter functionality coming soon\')"><i class="bi bi-funnel me-1"></i>Filter</button>'),
        ('<button class="action-btn secondary"><i class="bi bi-sort-down me-1"></i>Sort</button>', '<button class="action-btn secondary" onclick="alert(\'Sort functionality coming soon\')"><i class="bi bi-sort-down me-1"></i>Sort</button>'),
        ('<button class="action-btn primary"><i class="bi bi-person-plus-fill me-1"></i>Enroll Student</button>', '<button class="action-btn primary" onclick="alert(\'Enrollment via Dashboard is coming soon. Please use Mobile App to register.\')"><i class="bi bi-person-plus-fill me-1"></i>Enroll Student</button>'),
    ],
    "backend/dashboard/templates/transactions.html": [
        ('<button class="action-btn secondary" type="button"><i class="bi bi-download me-1"></i>Export CSV</button>', '<button class="action-btn secondary" type="button" onclick="exportTransactionsCSV()"><i class="bi bi-download me-1"></i>Export CSV</button>'),
        ('<button class="action-btn secondary" type="button"><i class="bi bi-printer me-1"></i>Print</button>', '<button class="action-btn secondary" type="button" onclick="window.print()"><i class="bi bi-printer me-1"></i>Print</button>')
    ],
    "backend/dashboard/templates/products.html": [
        ('<button type="button" class="upload-button"><i class="bi bi-camera-fill d-block"></i>Upload</button>', '<button type="button" class="upload-button" onclick="document.getElementById(\'productImageInput\').click()"><i class="bi bi-camera-fill d-block"></i>Upload</button>')
    ],
    "backend/dashboard/templates/fraud_alerts.html": [
        ('<button class="sidebar-cta" type="button"><i class="bi bi-plus-circle me-1"></i>New Transaction</button>', '<a href="/transactions" class="sidebar-cta" style="text-decoration:none;display:flex;align-items:center;justify-content:center"><i class="bi bi-plus-circle me-1"></i>New Transaction</a>'),
        ('<button class="action-btn secondary"><i class="bi bi-download me-1"></i>Export Log</button>', '<button class="action-btn secondary" onclick="alert(\'Export functionality coming soon\')"><i class="bi bi-download me-1"></i>Export Log</button>'),
        ('<button type="button"><strong>Suspend New Card</strong><br><small class="text-muted">Instantly block any credential</small></button>', '<button type="button" data-bs-toggle="modal" data-bs-target="#suspendModal"><strong>Suspend New Card</strong><br><small class="text-muted">Instantly block any credential</small></button>'),
        ('<button type="button"><strong>Risk Audit Log</strong><br><small class="text-muted">Review last 48 hours of activity</small></button>', '<button type="button" onclick="window.location.href=\'/transactions?type=void\'"><strong>Risk Audit Log</strong><br><small class="text-muted">Review last 48 hours of activity</small></button>'),
        ('<button type="button"><strong>Seton Intelligence Beta</strong><br><small class="text-muted">ML-driven threat detection</small></button>', '<button type="button" onclick="alert(\'Seton Intelligence is currently analyzing background traffic.\')"><strong>Seton Intelligence Beta</strong><br><small class="text-muted">ML-driven threat detection</small></button>')
    ],
    "backend/cashier_app/templates/cashier_index_standalone.html": [
        ('<button class="icon-circle" title="View mode"><i class="bi bi-grid-3x3-gap-fill"></i></button>', '<button class="icon-circle" title="View mode" onclick="document.querySelector(\'.products-grid\').classList.toggle(\'list-view\')"><i class="bi bi-grid-3x3-gap-fill"></i></button>')
    ]
}

for file_path, replacements in files.items():
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for old, new in replacements:
            content = content.replace(old, new)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file_path}")
    except Exception as e:
        print(f"Error {file_path}: {e}")
