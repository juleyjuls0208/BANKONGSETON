"""Generate Bangko ng Seton PWA icons from the official school crest."""
from pathlib import Path

from PIL import Image


SIZES = [72, 96, 128, 144, 152, 192, 384, 512]


def create_icon(crest: Image.Image, size: int) -> Image.Image:
    """Contain the complete crest inside a square, install-safe white canvas."""
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    max_width = max(1, int(size * 0.88))
    max_height = max(1, int(size * 0.78))
    scale = min(max_width / crest.width, max_height / crest.height)
    resized = crest.resize(
        (max(1, round(crest.width * scale)), max(1, round(crest.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas.alpha_composite(resized, ((size - resized.width) // 2, (size - resized.height) // 2))
    return canvas.convert("RGB")


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    source_path = script_dir / "static" / "seton_logo.png"
    icons_dir = script_dir / "static" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    crest = Image.open(source_path).convert("RGBA")
    crest = crest.crop(crest.getbbox())

    print("Generating PWA icons from seton_logo.png...")
    for size in SIZES:
        output_path = icons_dir / f"icon-{size}x{size}.png"
        create_icon(crest, size).save(output_path, "PNG", optimize=True)
        print(f"  created {output_path.name}")

    print(f"Generated {len(SIZES)} icons in {icons_dir}")


if __name__ == "__main__":
    main()
