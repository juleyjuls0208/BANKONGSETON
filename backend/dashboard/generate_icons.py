"""
Generate PWA icons for Bangko ng Seton
Creates simple colored icons with text
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Icon sizes needed for PWA
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

# Colors
BG_COLOR = (79, 70, 229)  # Indigo-600
TEXT_COLOR = (255, 255, 255)  # White

def create_icon(size):
    """Create a simple icon with B logo"""
    # Create image
    img = Image.new('RGB', (size, size), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Draw "B" in the center
    font_size = int(size * 0.6)
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default
        font = ImageFont.load_default()
    
    text = "B"
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (size - text_width) / 2
    y = (size - text_height) / 2 - bbox[1]
    
    # Draw text
    draw.text((x, y), text, fill=TEXT_COLOR, font=font)
    
    return img

def main():
    """Generate all icon sizes"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, 'static', 'icons')
    
    # Create icons directory
    os.makedirs(icons_dir, exist_ok=True)
    
    print("Generating PWA icons...")
    
    for size in SIZES:
        filename = f"icon-{size}x{size}.png"
        filepath = os.path.join(icons_dir, filename)
        
        icon = create_icon(size)
        icon.save(filepath, 'PNG')
        
        print(f"  ✓ Created {filename}")
    
    print(f"\n✅ Generated {len(SIZES)} icons in {icons_dir}")

if __name__ == '__main__':
    main()
