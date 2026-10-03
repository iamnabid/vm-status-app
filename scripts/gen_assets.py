"""Generate favicon.ico and og-image.png for nabidsheikh.systems.

One-off asset generator, not part of the deploy pipeline. Re-run manually
if the palette or copy changes.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

BG = (13, 27, 30)          # --bg
PANEL = (20, 43, 46)       # --panel
LINE = (36, 57, 60)        # --line
BRASS = (199, 162, 90)     # --brass
BRASS_DIM = (140, 116, 64) # --brass-dim
INK = (237, 230, 214)      # --ink
DIM = (124, 148, 150)      # --dim

FONTS = Path("C:/Windows/Fonts")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def gen_favicon():
    size = 256
    img = Image.new("RGBA", (size, size), BG + (255,))
    draw = ImageDraw.Draw(img)
    # Rounded-square panel, matching the site's .panel/.seg radius language
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=40, fill=BG)
    r = size * 0.27
    cx = cy = size / 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BRASS)
    out_ico = STATIC / "favicon.ico"
    img.save(out_ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print(f"wrote {out_ico}")

    out_svg = STATIC / "favicon.svg"
    out_svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" rx="6" fill="#0d1b1e"/>'
        '<circle cx="16" cy="16" r="8.6" fill="#c7a25a"/>'
        "</svg>\n",
        encoding="utf-8",
    )
    print(f"wrote {out_svg}")


def gen_og_image():
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    # Subtle diagonal hairline texture, echoing the site's background-image
    for x in range(-h, w, 8):
        draw.line([(x, 0), (x + h, h)], fill=(18, 35, 38), width=1)

    margin = 90
    draw.rectangle([margin, margin, w - margin, h - margin], outline=LINE, width=2)

    # Status dot, top-left of the frame, matching the live-status motif
    dot_r = 9
    dot_cx, dot_cy = margin + 46, margin + 46
    draw.ellipse(
        [dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=BRASS
    )

    name_font = font("georgiab.ttf", 74)
    role_font = font("consola.ttf", 30)
    tag_font = font("consola.ttf", 24)

    draw.text((margin + 74, margin + 20), "Nabid Sheikh", font=name_font, fill=INK)
    draw.text(
        (margin + 76, margin + 112),
        "Environmental engineering \u00b7 remote sensing \u00b7 infrastructure",
        font=role_font,
        fill=BRASS,
    )

    lines = [
        "CZU Prague \u2014 snow cover trends across Czech mountain ranges",
        "Cloud infra, CI/CD, and systems work behind the research",
    ]
    y = margin + 190
    for line in lines:
        draw.text((margin + 76, y), line, font=tag_font, fill=DIM)
        y += 38

    tag = "nabidsheikh.systems"
    tag_w = draw.textlength(tag, font=tag_font)
    draw.text(
        (w - margin - tag_w - 6, h - margin - 40), tag, font=tag_font, fill=BRASS_DIM
    )

    out = STATIC / "og-image.png"
    img.save(out, format="PNG")
    print(f"wrote {out}")


if __name__ == "__main__":
    STATIC.mkdir(exist_ok=True)
    gen_favicon()
    gen_og_image()
