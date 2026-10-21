#!/usr/bin/env python3
"""
Generate profile-ascii.svg from source-prepped.png.

source-prepped.png is already a high-contrast B&W portrait — ideal for ASCII.
Strategy:
  • High resolution grid (160 cols × 130 rows) to capture fine detail
  • Blend grayscale + edge map so outlines (hair curls, eyes, jaw) are crisp
  • Inverted ramp: dark image pixel → dense/bright char on dark SVG background
  • Correct monospace aspect ratio compensation
"""
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np
import os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src  = os.path.join(ROOT, "source-prepped.png")   # already B&W, high contrast
out  = os.path.join(ROOT, "profile-ascii.svg")

# ── 1. Load ────────────────────────────────────────────────────────────────
img = Image.open(src).convert("L")   # already grayscale, just ensure L mode

# ── 2. Crop tightly around the subject (remove excess white border) ────────
# source-prepped has a white background; crop to bounding box of non-white
arr_full = np.array(img)
mask = arr_full < 245                         # non-white pixels
rows_nz = np.where(mask.any(axis=1))[0]
cols_nz = np.where(mask.any(axis=0))[0]
if rows_nz.size and cols_nz.size:
    pad = 20  # px padding
    r0 = max(0, rows_nz[0]  - pad)
    r1 = min(arr_full.shape[0], rows_nz[-1]  + pad)
    c0 = max(0, cols_nz[0]  - pad)
    c1 = min(arr_full.shape[1], cols_nz[-1] + pad)
    img = img.crop((c0, r0, c1, r1))

# ── 3. Pre-process ────────────────────────────────────────────────────────
# The source is already great — just boost contrast a bit more
img = ImageOps.autocontrast(img, cutoff=1)
img = ImageEnhance.Contrast(img).enhance(1.4)
img = ImageEnhance.Sharpness(img).enhance(2.0)   # sharpen edges

# ── 4. Build edge map and blend with base ─────────────────────────────────
edges = img.filter(ImageFilter.FIND_EDGES)
edges = ImageEnhance.Brightness(edges).enhance(3.0)  # amplify edges
# Blend: darken base image where edges are prominent → crisper features
base_arr  = np.array(img).astype(float)
edge_arr  = np.array(edges).astype(float)
# Darken pixels at edges (edge overlay makes them go to black → dense chars)
blended = np.clip(base_arr - edge_arr * 0.6, 0, 255).astype(np.uint8)
img = Image.fromarray(blended)

# ── 5. Resize to ASCII grid ───────────────────────────────────────────────
# Monospace char aspect: width ≈ 0.55 × font-size, height ≈ 1.18 × font-size
# char_w/char_h ≈ 0.55/1.18 ≈ 0.466
# To preserve image proportions: ROWS = COLS × (img_h/img_w) × char_w/char_h
#
# We want width coverage across ~832 SVG units at font_size=4.2
# Each char takes ~4.2*0.55 = 2.31px wide → textLength=832 / 2.31 ≈ 360 … 
# but we use textLength+lengthAdjust so we can freely choose COLS.
# With COLS=160, each SVG char slot = 832/160 = 5.2px wide, height = 4.2*1.18 = 4.96px
# Aspect of one slot: 5.2/4.96 = 1.048 (slightly wider than tall — good)
#
# Source image after crop is roughly square (portrait slightly taller).
# img_aspect = W/H.  We want:  COLS / ROWS = img_aspect × (slot_h/slot_w)
# slot_h/slot_w = 4.96/5.2 = 0.954
# ROWS = COLS / (img_aspect × 0.954)

COLS = 130
w_c, h_c = img.size
img_aspect = w_c / h_c
ROWS = max(60, int(round(COLS / (img_aspect * 0.954))))

arr = np.array(
    img.resize((COLS, ROWS), Image.Resampling.LANCZOS)
).astype(float) / 255.0

# ── 6. Tone mapping ───────────────────────────────────────────────────────
# source-prepped background is white (1.0) → should become spaces.
# dark pixels (hair, outlines) = 0.0 → should become densest chars.
# Apply mild gamma to preserve midtone detail in face.
arr = np.power(arr, 0.80)

# ── 7. Map luminance → ASCII ramp ─────────────────────────────────────────
# dark bg SVG: lum=0 (black in image) → dense bright char; lum=1 (white) → space
RAMP = " .`'^\",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
N = len(RAMP)

# White background threshold: anything above 0.92 → force space
WHITE_THRESH = 0.92

lines = []
for row in arr:
    chars = []
    for lum in row:
        if lum >= WHITE_THRESH:
            chars.append(" ")
        else:
            # map [0, WHITE_THRESH] → [N-1, 0]  (dark=dense, light=sparse)
            idx = int((1.0 - lum / WHITE_THRESH) * (N - 1))
            idx = max(0, min(N - 1, idx))
            chars.append(RAMP[idx])
    lines.append("".join(chars))

# ── 8. Build SVG ──────────────────────────────────────────────────────────
SVG_W    = 860
FONT_SZ  = 4.8
LINE_H   = FONT_SZ * 1.18
TEXT_X   = 14
TEXT_W   = SVG_W - TEXT_X * 2
TOP_BAR  = 40
TEXT_Y0  = TOP_BAR + FONT_SZ + 8
BOT_PAD  = 32
SVG_H    = int(TEXT_Y0 + ROWS * LINE_H + BOT_PAD)

parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">',
    f'<rect width="{SVG_W}" height="{SVG_H}" rx="10" fill="#0d1117"/>',
    f'<rect x=".5" y=".5" width="{SVG_W-1}" height="{SVG_H-1}" rx="10" fill="none" stroke="#30363d"/>',
    f'<line x1="0" y1="{TOP_BAR}" x2="{SVG_W}" y2="{TOP_BAR}" stroke="#30363d"/>',
    # traffic-light dots
    '<circle cx="18" cy="20" r="5" fill="#ff5f56"/>',
    '<circle cx="36" cy="20" r="5" fill="#ffbd2e"/>',
    '<circle cx="54" cy="20" r="5" fill="#27c93f"/>',
    # title
    f'<text x="{SVG_W//2}" y="26" text-anchor="middle" '
    f'font-family="SFMono-Regular,Consolas,DejaVu Sans Mono,monospace" '
    f'font-size="12" fill="#8b949e">Manohar-P-C@github: ~/portrait.sh</text>',
]

for y, line in enumerate(lines):
    ty = TEXT_Y0 + y * LINE_H
    parts.append(
        f'<text x="{TEXT_X}" y="{ty:.2f}" '
        f'fill="#c9d1d9" '
        f'font-family="SFMono-Regular,Consolas,DejaVu Sans Mono,monospace" '
        f'font-size="{FONT_SZ}" xml:space="preserve" '
        f'textLength="{TEXT_W}" lengthAdjust="spacingAndGlyphs">'
        f'{html.escape(line)}</text>'
    )

BOT_Y = int(TEXT_Y0 + ROWS * LINE_H + 8)
parts += [
    f'<line x1="0" y1="{BOT_Y}" x2="{SVG_W}" y2="{BOT_Y}" stroke="#30363d"/>',
    f'<text x="{TEXT_X}" y="{BOT_Y + 18}" '
    f'font-family="SFMono-Regular,Consolas,DejaVu Sans Mono,monospace" '
    f'font-size="11" fill="#8b949e">portrait generated from source-photo.png</text>',
    '</svg>',
]

with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(parts))

print(f"Generated {out}  ({COLS}×{ROWS} chars, SVG {SVG_W}×{SVG_H})")
