import re

files = {
    "backend/dashboard/templates/students.html": (
        r'<div class="pager">.*?</div>',
        '<div class="pager" style="display:none;"><!-- Pagination not yet implemented --></div>'
    ),
    "backend/dashboard/templates/transactions.html": (
        r'<div class="pager">.*?</div>',
        '<div class="pager" style="display:none;"><!-- Pagination not yet implemented --></div>'
    )
}

for file_path, (pattern, replacement) in files.items():
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # also fix the chevron buttons in students.html
        if 'students.html' in file_path:
            content = content.replace(
                '<td><button class="icon-btn"><i class="bi bi-chevron-right"></i></button></td>',
                '<td><button class="icon-btn" onclick="window.location.href=\'/transactions?q=\' + encodeURIComponent(\'${esc(s.StudentID)}\')"><i class="bi bi-clock-history"></i></button></td>'
            )
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated pagination in {file_path}")
    except Exception as e:
        print(f"Error {file_path}: {e}")
