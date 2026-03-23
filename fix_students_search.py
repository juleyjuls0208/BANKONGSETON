import re

file_path = "backend/dashboard/templates/students.html"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make search functional by binding it to input
if "searchInput.addEventListener('input'" not in content:
    content = content.replace(
        "document.addEventListener('DOMContentLoaded', loadStudents);",
        """document.addEventListener('DOMContentLoaded', loadStudents);
    
    let searchDebounce;
    document.getElementById('searchInput').addEventListener('input', () => {
        clearTimeout(searchDebounce);
        searchDebounce = setTimeout(searchStudents, 300);
    });"""
    )
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added search debounce to students.html")
