import re

file_path = "backend/dashboard/templates/products.html"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure there is an input field for the image upload
if 'id="productImageInput"' not in content:
    upload_input = '<input type="file" id="productImageInput" accept="image/*" style="display: none;" onchange="handleImageUpload(event)">\n<div class="product-form-grid">'
    content = content.replace('<div class="product-form-grid">', upload_input, 1)

upload_script = """
let currentImageBase64 = null;

function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        currentImageBase64 = e.target.result;
        // Find the upload button and change its appearance to show an image was selected
        const uploadBtn = document.querySelector('.upload-button');
        if (uploadBtn) {
            uploadBtn.innerHTML = '<i class="bi bi-check-circle-fill text-success d-block"></i>Selected';
            uploadBtn.style.border = '2px dashed #10b981';
            uploadBtn.style.background = '#f0fdf4';
        }
    };
    reader.readAsDataURL(file);
}
"""

if "function handleImageUpload" not in content:
    content = content.replace("</script>\n{% endblock %}", upload_script + "\n</script>\n{% endblock %}")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated products.html to handle image uploads")
