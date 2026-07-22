"""Regenerate seton_logo.png: crisp, pure-black school seal at 1024x1024.

Composition (matches the original institution seal):
  - double-ring circle
  - two facing human profiles (curved, recognizable faces) leaving a central
    heart of negative space
  - a solid black ribbon banner with "MCMLXXV" carved out (transparent text)
"""
import math
from PIL import Image, ImageDraw, ImageFont

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
BLACK = (0, 0, 0, 255)
cx, cy = S // 2, int(S * 0.46)

# ---- rings ----
ring_r = 472
d.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=BLACK, width=24)
inner_r = 404
d.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], outline=BLACK, width=8)

def profile(facing_right):
    """Build a smooth profile polygon. facing_right=True -> nose points right."""
    f = 1 if facing_right else -1
    pts = []
    face = [
        (-10, -180),   # crown
        (-14, -150),
        (-6, -120),    # forehead bulge
        (-2, -95),
        (-30, -78),    # brow ridge (nose root pushed right)
        (-44, -58),    # nose bridge
        (-70, -40),    # nose tip
        (-44, -26),    # under nose
        (-40, -8),     # upper lip
        (-58, 6),      # lips out
        (-40, 22),     # lower lip
        (-46, 40),     # chin
        (-20, 64),     # under chin
        (-8, 90),      # jaw
        (-6, 130),     # neck front
        (-6, 180),     # neck bottom
    ]
    back = [
        (30, 180),     # neck back bottom (kept tight so profiles don't collide)
        (36, 120),
        (40, 60),
        (34, 0),       # back of head widest
        (20, -70),
        (6, -150),     # behind crown
        (0, -180),     # crown back
    ]
    contour = face + back
    # offset each profile outward from center so the two backs don't overlap
    off = 150
    for (x, y) in contour:
        px = cx + f * x + (off if not facing_right else -off)
        py = cy + y
        pts.append((px, py))
    return pts

# Left profile faces right (nose toward center), right profile faces left.
d.polygon(profile(facing_right=True), fill=BLACK)
d.polygon(profile(facing_right=False), fill=BLACK)

# tiny centered detail between the two faces (small black dash - "mouth")
d.rectangle([cx - 10, cy - 4, cx + 10, cy + 10], fill=BLACK)

# ---- banner ----
by = cy + 250
bh = 96
bw = 640
bx = cx - bw // 2
# fold ends
d.polygon([(bx + 8, by + 10), (bx - 40, by + bh // 2), (bx + 8, by + bh - 10)], fill=BLACK)
d.polygon([(bx + bw - 8, by + 10), (bx + bw + 40, by + bh // 2), (bx + bw - 8, by + bh - 10)], fill=BLACK)
# body
d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16, fill=BLACK)

# ---- carve MCMLXXV out of the banner (transparent text) ----
font = None
for cand in ["C:/Windows/Fonts/ARIALBD.TTF", "C:/Windows/Fonts/arialbd.ttf",
             "DejaVuSans-Bold.ttf", "arial.ttf"]:
    try:
        font = ImageFont.truetype(cand, 70)
        break
    except Exception:
        continue
if font is None:
    font = ImageFont.load_default()

txt = "MCMLXXV"
bbox = d.textbbox((0, 0), txt, font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
tx = cx - tw // 2 - bbox[0]
ty = by + bh // 2 - th // 2 - bbox[1]
# erase text from the black banner -> transparent cutout
d.text((tx, ty), txt, font=font, fill=(0, 0, 0, 0))

img.save("seton_logo.png", "PNG")
print("wrote seton_logo.png", img.size)
