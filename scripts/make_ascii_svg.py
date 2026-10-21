#!/usr/bin/env python3
"""
Generate profile-ascii.svg matching avi-ascii.svg terminal animation style.

Style features:
  • Skin rendered with NO ASCII characters (clean empty spaces)
  • Background rendered with NO ASCII characters (clean empty spaces)
  • Hair rendered with rich curly ASCII texture
  • Eyebrows, eyes, pupils, nose, lips, jawline, ears, and shirt stripes
    rendered with crisp ASCII characters
  • Animated terminal frame with row-by-row typing clipPath and moving cursor
  • Terminal header and whoami footer with blinking cursor
"""

import sys
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

WORKSPACE = Path(__file__).resolve().parent.parent
SOURCE_PATH = WORKSPACE / "source-photo.png"
OUTPUT_SVG = WORKSPACE / "profile-ascii.svg"

# Grid settings matching avi-ascii.svg
COLS = 180
ROWS = 96
SVG_W = 840.0
SVG_H = 880.0
CONTENT_W = 800.0
FONT_SIZE = 7.2
ROW_H = 8.3
ROW_DUR = 0.06
X_OFFSET = 20.0
Y_START_CLIP = 37.0
Y_START_TEXT = 43.2
Y_START_RECT = 38.0

RAMP = "@%#sc*+=-:` "


def process_portrait(img_path: Path):
    img = Image.open(img_path).convert("RGB")
    
    # 1. Tight crop matching Avi's head-and-shoulders framing
    # In 1254x1254 source photo:
    crop_box = (160, 40, 1040, 1040)  # 880 x 1000
    img_crop = img.crop(crop_box)
    w, h = img_crop.size

    arr_rgb = np.array(img_crop, dtype=np.float32)
    r = arr_rgb[:, :, 0]
    g = arr_rgb[:, :, 1]
    b = arr_rgb[:, :, 2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b

    # 2. Background mask (cream/off-white background)
    bg_sample = np.array([245.0, 240.0, 220.0])
    bg_dist = np.sqrt((r - bg_sample[0])**2 + (g - bg_sample[1])**2 + (b - bg_sample[2])**2)
    is_bg = (bg_dist < 45) | ((r > 230) & (g > 225) & (b > 205) & (np.abs(r - g) < 20))

    # 3. Multi-scale edge detection
    pil_gray = Image.fromarray(gray.astype(np.uint8))
    edges = np.array(pil_gray.filter(ImageFilter.FIND_EDGES))
    smooth_gray = pil_gray.filter(ImageFilter.GaussianBlur(radius=1.2))
    smooth_edges = np.array(smooth_gray.filter(ImageFilter.FIND_EDGES))
    comb_edges = np.maximum(edges, smooth_edges * 1.3)

    y_indices = np.arange(h)[:, None]
    x_indices = np.arange(w)[None, :]

    # 4. Hair mask (upper curly crown)
    is_hair = (y_indices < 620) & (gray < 85) & ~is_bg

    # 5. Facial features (eyebrows, eyes, eyelids, pupils, nostrils, lips)
    face_region = (y_indices >= 240) & (y_indices <= 760) & (x_indices >= 120) & (x_indices <= 780)
    is_feature = face_region & (gray < 75) & ~is_bg

    # 6. Ears
    ears_region = (y_indices >= 400) & (y_indices <= 640) & ((x_indices <= 260) | (x_indices >= 660))
    is_ear = ears_region & ((comb_edges > 20) | (gray < 70)) & ~is_bg

    # 7. Jawline and chin edge
    jaw_region = (y_indices >= 520) & (y_indices <= 770) & (x_indices >= 220) & (x_indices <= 720)
    is_jaw_edge = jaw_region & (comb_edges > 24) & ~is_bg

    # 8. Neck contours
    neck_region = (y_indices >= 650) & (y_indices <= 960) & ((x_indices <= 390) | (x_indices >= 580))
    is_neck_edge = neck_region & (comb_edges > 20) & ~is_bg

    # 9. Shirt & collar
    collar_outline = (y_indices >= 760) & (y_indices <= 880) & (comb_edges > 20) & ~is_bg
    is_shirt_area = (y_indices >= 820) & ~is_bg
    is_neck_skin = (y_indices >= 650) & (y_indices < 860) & (x_indices >= 320) & (x_indices <= 650)
    green_stripes = is_shirt_area & (gray < 120) & ~is_neck_skin & ~is_bg

    # Assemble line art canvas (default pure white 255)
    canvas = np.full_like(gray, 255)

    # Hair
    canvas[is_hair] = gray[is_hair]
    # Ears
    canvas[is_ear] = np.minimum(canvas[is_ear], gray[is_ear])
    # Facial features
    canvas[is_feature] = np.minimum(canvas[is_feature], gray[is_feature])
    # Jawline and neck
    canvas[is_jaw_edge] = np.minimum(canvas[is_jaw_edge], 40)
    canvas[is_neck_edge] = np.minimum(canvas[is_neck_edge], 40)
    # Collar & shirt stripes
    canvas[collar_outline] = np.minimum(canvas[collar_outline], 30)
    canvas[green_stripes] = np.minimum(canvas[green_stripes], gray[green_stripes])

    # 10. Blank out skin:
    # Ensure skin that is not a sharp feature/edge is 100% pure white (no ASCII)
    is_skin = (r > 90) & (g > 55) & (b > 35) & (r >= g) & (g >= b) & ((r - b) >= 18) & ~is_bg
    # Forehead shadow / cheek shadow erasure:
    skin_smooth = is_skin & (gray >= 70) & (comb_edges < 35)
    canvas[skin_smooth] = 255

    # 11. Blank out background
    canvas[is_bg] = 255

    line_art_img = Image.fromarray(canvas.astype(np.uint8))

    # 12. Thicken dark lines slightly with MinFilter(3)
    # This prevents sub-pixel thin lines from disappearing during downsampling
    thickened_art = line_art_img.filter(ImageFilter.MinFilter(3))

    # 13. Downsample to target COLS x ROWS
    small_art = thickened_art.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    arr_small = np.array(small_art)

    # Convert to ASCII
    def val_to_char(val):
        if val >= 215:
            return " "
        idx = int((val / 215.0) * (len(RAMP) - 1))
        return RAMP[min(idx, len(RAMP) - 2)]

    ascii_lines = []
    for r_i in range(ROWS):
        line = "".join(val_to_char(arr_small[r_i, c]) for c in range(COLS))
        ascii_lines.append(line)

    return ascii_lines


def build_svg(ascii_lines):
    svg_parts = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" '
        f'viewBox="0 0 {SVG_W} {SVG_H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">\n'
    )
    svg_parts.append(
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/>'
        "</linearGradient></defs>\n"
    )
    svg_parts.append(f'<rect width="{SVG_W}" height="{SVG_H}" rx="12" fill="url(#bg)"/>\n')
    svg_parts.append(
        f'<rect x="0.5" y="0.5" width="{SVG_W - 1}" height="{SVG_H - 1}" rx="12" '
        'fill="none" stroke="#30363d" stroke-width="1"/>\n'
    )
    svg_parts.append(f'<line x1="0" y1="30" x2="{SVG_W}" y2="30" stroke="#30363d"/>\n')
    svg_parts.append('<circle cx="20" cy="15.0" r="5" fill="#ff5f56"/>\n')
    svg_parts.append('<circle cx="36" cy="15.0" r="5" fill="#ffbd2e"/>\n')
    svg_parts.append('<circle cx="52" cy="15.0" r="5" fill="#27c93f"/>\n')
    svg_parts.append(
        f'<text x="{SVG_W / 2}" y="19.0" fill="#7d8590" font-size="12" text-anchor="middle">'
        "Manohar-P-C@github: ~$ ./portrait.sh</text>\n"
    )

    char_w = CONTENT_W / COLS

    for i, line in enumerate(ascii_lines):
        t_begin = i * ROW_DUR
        t_end = (i + 1) * ROW_DUR
        y_clip = Y_START_CLIP + i * ROW_H
        y_text = Y_START_TEXT + i * ROW_H
        y_rect = Y_START_RECT + i * ROW_H

        # ClipPath
        svg_parts.append(
            f'<clipPath id="r{i}"><rect x="{X_OFFSET}" y="{y_clip:.1f}" height="{ROW_H:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{CONTENT_W}" begin="{t_begin:.3f}s" '
            f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>\n'
        )

        # Text line
        svg_parts.append(
            f'<g clip-path="url(#r{i})"><text xml:space="preserve" x="{X_OFFSET}" y="{y_text:.1f}" '
            f'fill="#c9d1d9" font-size="{FONT_SIZE}" textLength="{CONTENT_W}" '
            f'lengthAdjust="spacing">{line}</text></g>\n'
        )

        # Scanning cursor
        svg_parts.append(
            f'<rect y="{y_rect:.1f}" width="{char_w:.3f}" height="{ROW_H - 2:.2f}" '
            f'fill="#c9d1d9" opacity="0">'
            f'<animate attributeName="x" from="{X_OFFSET}" to="{X_OFFSET + CONTENT_W}" '
            f'begin="{t_begin:.3f}s" dur="{ROW_DUR:.2f}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0.85" begin="{t_begin:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{t_end:.3f}s"/></rect>\n'
        )

    # Footer
    svg_parts.append(f'<line x1="0" y1="837.0" x2="{SVG_W}" y2="837.0" stroke="#30363d"/>\n')
    svg_parts.append(
        '<text x="20" y="856.0" fill="#7d8590" font-size="13">'
        'Manohar-P-C@github:~$ whoami <tspan fill="#c9d1d9">Manohar P C</tspan></text>\n'
    )
    # Cursor after "Manohar P C" (starts at x=20, text length ~41 chars monospace ≈ 348px)
    svg_parts.append(
        '<rect x="348.0" y="844.0" width="8" height="14" fill="#c9d1d9">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>'
        "</rect>\n"
    )
    svg_parts.append("</svg>\n")

    return "".join(svg_parts)


def main():
    print(f"Loading {SOURCE_PATH}...")
    ascii_lines = process_portrait(SOURCE_PATH)
    print(f"Generated {len(ascii_lines)} rows x {len(ascii_lines[0])} cols")

    svg_content = build_svg(ascii_lines)
    OUTPUT_SVG.write_text(svg_content, encoding="utf-8")
    print(f"Successfully generated {OUTPUT_SVG} ({len(svg_content):,} bytes)")


if __name__ == "__main__":
    main()
