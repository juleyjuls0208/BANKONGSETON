import re

file_path = "backend/dashboard/templates/students.html"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I am going to store global state for students
state_script = """
    let allStudents = [];
    let currentSort = { field: 'Name', asc: true };
    let currentFilter = 'all'; // all, active, lost
    
    function setStudents(students) {
        allStudents = students;
        applySortAndFilter();
    }
    
    function toggleSort() {
        if (currentSort.field === 'Name') {
            currentSort = { field: 'Balance', asc: false };
        } else if (currentSort.field === 'Balance') {
            currentSort = { field: 'Name', asc: true };
        }
        applySortAndFilter();
    }
    
    function toggleFilter() {
        if (currentFilter === 'all') currentFilter = 'active';
        else if (currentFilter === 'active') currentFilter = 'lost';
        else currentFilter = 'all';
        
        const btn = document.getElementById('filterBtn');
        if (btn) {
            if (currentFilter === 'all') btn.innerHTML = '<i class="bi bi-funnel me-1"></i>Filter';
            else if (currentFilter === 'active') btn.innerHTML = '<i class="bi bi-funnel-fill text-success me-1"></i>Active Only';
            else btn.innerHTML = '<i class="bi bi-funnel-fill text-danger me-1"></i>Lost Cards';
        }
        applySortAndFilter();
    }
    
    function applySortAndFilter() {
        let filtered = [...allStudents];
        
        if (currentFilter === 'active') {
            filtered = filtered.filter(s => String(s.Status || 'Active').toLowerCase() === 'active');
        } else if (currentFilter === 'lost') {
            filtered = filtered.filter(s => !String(s.MoneyCardNumber || '').trim());
        }
        
        filtered.sort((a, b) => {
            if (currentSort.field === 'Name') {
                const nameA = String(a.Name || '').toLowerCase();
                const nameB = String(b.Name || '').toLowerCase();
                return currentSort.asc ? nameA.localeCompare(nameB) : nameB.localeCompare(nameA);
            } else if (currentSort.field === 'Balance') {
                const balA = Number(a.Balance || 0);
                const balB = Number(b.Balance || 0);
                return currentSort.asc ? balA - balB : balB - balA;
            }
            return 0;
        });
        
        displayStudents(filtered, false);
    }
"""

if "let allStudents =" not in content:
    content = content.replace("<script>", "<script>\n" + state_script)
    content = content.replace("displayStudents(data.students || []);", "setStudents(data.students || []);")
    
    # update the displayStudents signature
    content = content.replace("function displayStudents(students) {", "function displayStudents(students, updateGlobal = true) {\n        if (updateGlobal) allStudents = students;\n")
    
    # fix the buttons
    content = content.replace('<button class="action-btn secondary" onclick="alert(\'Filter functionality coming soon\')"><i class="bi bi-funnel me-1"></i>Filter</button>',
                              '<button id="filterBtn" class="action-btn secondary" onclick="toggleFilter()"><i class="bi bi-funnel me-1"></i>Filter</button>')
    content = content.replace('<button class="action-btn secondary" onclick="alert(\'Sort functionality coming soon\')"><i class="bi bi-sort-down me-1"></i>Sort</button>',
                              '<button class="action-btn secondary" onclick="toggleSort()"><i class="bi bi-sort-down me-1"></i>Sort</button>')

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added sort and filter logic to students.html")
