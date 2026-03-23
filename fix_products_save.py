import re

file_path = "backend/dashboard/templates/products.html"
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add handling of the currentImageBase64 to saveProduct and reset it in openAddModal
if "currentImageBase64 = null;" in content:
    content = content.replace("function openAddModal() {\n", "function openAddModal() {\n    currentImageBase64 = null;\n    resetImageUploadButton();\n")
    content = content.replace("function openEditModal(id) {\n", "function openEditModal(id) {\n    currentImageBase64 = null;\n    resetImageUploadButton();\n")

reset_script = """
function resetImageUploadButton() {
    const uploadBtn = document.querySelector('.upload-button');
    if (uploadBtn) {
        uploadBtn.innerHTML = '<i class="bi bi-camera-fill d-block"></i>Upload';
        uploadBtn.style.border = '';
        uploadBtn.style.background = '';
    }
    const fileInput = document.getElementById('productImageInput');
    if (fileInput) fileInput.value = '';
}
"""

if "function resetImageUploadButton" not in content:
    content = content.replace("</script>\n{% endblock %}", reset_script + "\n</script>\n{% endblock %}")

# Make sure we include currentImageBase64 in the payload if it exists
if "const payload = {" in content and "currentImageBase64" not in content.split("const payload = {")[1].split("}")[0]:
    content = re.sub(
        r'(const payload = {[^}]+)(};)',
        r'\1    image_base64: currentImageBase64 || undefined,\n\2',
        content
    )

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated products.html save logic")
