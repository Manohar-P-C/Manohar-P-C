#!/usr/bin/env python3
"""
Generate profile-ascii.svg from source-photo.png.
Produces a dense, high-contrast terminal-style ASCII portrait
(dark background, bright characters) matching the reference style.
"""
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np
import os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src  = os.path.join(ROOT, "source-photo.png")
out  = os.path.join(ROOT, "profile-ascii.svg")

# ── 1. Load & pre-process ──────────────────────────────────────────────────
img = Image.open(src).convert("RGB")

# Light edge-sharpening to make facial features crisp in ASCII
img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))

# Convert to grayscale
img = ImageOps.grayscale(img)

# Strong contrast stretch so the background becomes pure white and
# face tones are spread across the full ramp
img = ImageOps.autocontrast(img, cutoff=2)
img = ImageEnhance.Contrast(img).enhance(1.6)

# ── 2. Resize ──────────────────────────────────────────────────────────────
# Characters are taller than wide (~2:1), so we double the column count
# relative to rows to keep proportions square.
COLS = 200   # horizontal characters
ROWS = 100   # vertical lines  (2:1 aspect ratio compensation)

arr = np.asarray(
    img.resize((COLS, ROWS), Image.Resampling.LANCZOS)
).astype(float) / 255.0

# ── 3. Gamma / tone mapping ────────────────────────────────────────────────
# Raise highlights (push light areas to white = spaces) while
# keeping midtones varied → more detail in face.
arr = np.power(arr, 0.75)

# ── 4. Map luminance → ASCII character ────────────────────────────────────
# Dense ramp: space = lightest (background), '$' = darkest (hair/shadow)
# This is an "inverted" mapping because the SVG has a dark background –
# dark pixels in the image should become dense/bright chars.
RAMP = (
    " .`'^\",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
)
N = len(RAMP)

lines = []
for row in arr:
    chars = []
    for lum in row:
        if lum > 0.94:
            chars.append(" ")
        else:
            # lum=0 → darkest char, lum≈0.94 → space
            idx = int((1.0 - lum / 0.94) * (N - 1))
            idx = max(0, min(N - 1, idx))
            chars.append(RAMP[idx])
    lines.append("".join(chars))

# ── 5. Build SVG ──────────────────────────────────────────────────────────
SVG_W   = 860
FONT_SZ = 4.2          # px – smaller font → more detail
LINE_H  = FONT_SZ * 1.18
TEXT_X  = 14
TEXT_W  = SVG_W - TEXT_X * 2
TOP_BAR = 40
TEXT_Y0 = TOP_BAR + FONT_SZ + 6   # y of first text row

# Compute total height dynamically
BOT_BAR_H = 30                     # space for footer text
SVG_H = int(TEXT_Y0 + ROWS * LINE_H + BOT_BAR_H + 10)

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">',
    # dark background
    f'<rect width="{SVG_W}" height="{SVG_H}" rx="10" fill="#0d1117"/>',
    # border
    f'<rect x=".5" y=".5" width="{SVG_W-1}" height="{SVG_H-1}" rx="10" fill="none" stroke="#30363d"/>',
    # title bar separator
    f'<line x1="0" y1="{TOP_BAR}" x2="{SVG_W}" y2="{TOP_BAR}" stroke="#30363d"/>',
    # title text – match the README terminal theme
    f'<text x="{SVG_W//2}" y="25" text-anchor="middle" '
    f'font-family="SFMono-Regular,Consolas,DejaVu Sans Mono,monospace" '
    f'font-size="12" fill="#8b949e">Manohar-P-C@github: ~/portrait.sh</text>',
    # traffic-light dots (purely decorative)
    '<circle cx="18" cy="20" r="5" fill="#ff5f56"/>',
    '<circle cx="36" cy="20" r="5" fill="#ffbd2e"/>',
    '<circle cx="54" cy="20" r="5" fill="#27c93f"/>',
]

for y, line in enumerate(lines):
    ty = TEXT_Y0 + y * LINE_H
    escaped = html.escape(line)
    parts.append(
        f'<text x="{TEXT_X}" y="{ty:.2f}" '
        f'fill="#c9d1d9" '
        f'font-family="SFMono-Regular,Consolas,DejaVu Sans Mono,monospace" '
        f'font-size="{FONT_SZ}" xml:space="preserve" '
        f'textLength="{TEXT_W}" lengthAdjust="spacingAndGlyphs">'
        f'{escaped}</text>'
    )

# bottom bar
BOT_Y = int(TEXT_Y0 + ROWS * LINE_H + 8)
parts += [
    f'<line x1="0" y1="{BOT_Y}" x2="{SVG_W}" y2="{BOT_Y}" stroke="#30363d"/>',
    f'<text x="{TEXT_X}" y="{BOT_Y + 18}" '
    f'font-family="SFMono-Regular,Consolas,DejaVu Sans Mono,monospace" '
    f'font-size="11" fill="#8b949e">portrait generated from source-photo.png</text>',
    '</svg>',
]

svg_content = "\n".join(parts)
with open(out, "w", encoding="utf-8") as f:
    f.write(svg_content)

print(f"Generated {out}  ({COLS}×{ROWS} chars)")
