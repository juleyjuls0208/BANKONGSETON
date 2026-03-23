import re

file_path = "backend/dashboard/templates/transactions.html"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add exportTransactionsCSV function
export_script = """
function exportTransactionsCSV() {
    const table = document.getElementById('transactionsTable');
    if (!table || table.rows.length === 0 || table.rows[0].cells.length === 1) {
        alert('No transactions to export');
        return;
    }
    
    let csv = 'ID,Date,Student,Type,Amount,Status\n';
    
    // We only have the DOM or the global variable. It's better to fetch all or use the loaded ones.
    // For simplicity, just alert that it's a placeholder if it's too complex, or implement a basic one.
    // Let's implement a basic one based on current table rows:
    for (let i = 0; i < table.rows.length; i++) {
        let row = table.rows[i];
        let cols = row.cells;
        if (cols.length >= 6) {
            let id = cols[0].innerText.trim();
            let date = cols[1].innerText.trim();
            let student = cols[2].innerText.trim();
            let type = cols[3].innerText.trim();
            let amount = cols[4].innerText.trim().replace(/,/g, ''); // remove commas in amount
            let status = cols[5].innerText.trim();
            
            // Escape quotes
            id = '"' + id.replace(/"/g, '""') + '"';
            date = '"' + date.replace(/"/g, '""') + '"';
            student = '"' + student.replace(/"/g, '""') + '"';
            
            csv += [id, date, student, type, amount, status].join(',') + '\n';
        }
    }
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'transactions_export_' + new Date().toISOString().split('T')[0] + '.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
"""

if "function exportTransactionsCSV" not in content:
    content = content.replace("</script>\n{% endblock %}", export_script + "\n</script>\n{% endblock %}")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added exportTransactionsCSV to transactions.html")
else:
    print("exportTransactionsCSV already exists")
