import re

file_path = "backend/dashboard/templates/students.html"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make it show more than 10 students when filtering
content = content.replace('students.slice(0, 10).map(s => {', 'students.slice(0, 50).map(s => {')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated student limits")
