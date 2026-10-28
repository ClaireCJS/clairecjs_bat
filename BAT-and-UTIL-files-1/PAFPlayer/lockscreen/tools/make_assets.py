"""Generate the lock-screen companion's local vector-like PNG assets."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parents[1] / "Assets"
ASSETS.mkdir(exist_ok=True)


def icon(size, path):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = max(2, size // 12)
    draw.rounded_rectangle((margin, margin, size - margin, size - margin),
                           radius=size // 5, fill=(18, 38, 72, 255))
    center = size // 2
    stroke = max(2, size // 20)
    draw.arc((size // 4, size // 4, 3 * size // 4, 3 * size // 4),
             220, 500, fill=(82, 222, 224, 255), width=stroke)
    draw.line((center + size // 9, center - size // 5,
               center + size // 9, center + size // 6),
              fill=(255, 255, 255, 255), width=stroke)
    draw.ellipse((center - size // 15, center + size // 9,
                  center + size // 9, center + size // 4),
                 fill=(255, 255, 255, 255))
    image.save(ASSETS / path)


def banner(width, height, path):
    image = Image.new("RGBA", (width, height), (18, 38, 72, 255))
    draw = ImageDraw.Draw(image)
    unit = min(height * 3 // 4, width // 4)
    glyph = Image.open(ASSETS / "PAFIcon150.png")
    glyph = glyph.resize((unit, unit), Image.Resampling.LANCZOS)
    image.alpha_composite(glyph, (width // 2 - unit // 2, height // 2 - unit // 2))
    draw.line((0, height - 4, width, height - 4), fill=(82, 222, 224, 255), width=4)
    image.save(ASSETS / path)


badge = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
badge_draw = ImageDraw.Draw(badge)
badge_draw.line((13, 3, 13, 16), fill="white", width=3)
badge_draw.line((13, 3, 19, 5), fill="white", width=3)
badge_draw.ellipse((5, 13, 14, 22), fill="white")
badge.save(ASSETS / "PAFBadge.png")
for size in (44, 150):
    icon(size, f"PAFIcon{size}.png")
icon(50, "PAFStore50.png")
banner(310, 150, "PAFWide310.png")
banner(620, 300, "PAFSplash620.png")
