#!/usr/bin/env python3
"""Generate profile-ascii.svg from source-photo.png using Pillow."""
from PIL import Image, ImageOps, ImageEnhance
import numpy as np
import os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, "source-photo.png")
out = os.path.join(ROOT, "profile-ascii.svg")
img = Image.open(src).convert("RGB")
w, h = img.size
img = img.crop((int(w*.055), int(h*.02), int(w*.99), int(h*.995)))
img = ImageOps.grayscale(img)
img = ImageOps.autocontrast(img, cutoff=1)
img = ImageEnhance.Contrast(img).enhance(1.25)
arr = np.asarray(img.resize((170, 170), Image.Resampling.LANCZOS)).astype(float)/255
arr = np.power(arr, .88)
ramp = " .`^\",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
lines=[]
for row in arr:
    chars=[]
    for lum in row:
        if lum > .88: chars.append(" ")
        else: chars.append(ramp[max(0, min(len(ramp)-1, int((1-lum/.88)*(len(ramp)-1))))])
    lines.append("".join(chars))
parts=['<svg xmlns="http://www.w3.org/2000/svg" width="860" height="930" viewBox="0 0 860 930">',
'<rect width="860" height="930" rx="12" fill="#0d1117"/>',
'<rect x=".5" y=".5" width="859" height="929" rx="12" fill="none" stroke="#30363d"/>',
'<line x1="0" y1="40" x2="860" y2="40" stroke="#30363d"/>',
'<text x="430" y="24" text-anchor="middle" font-family="monospace" font-size="12" fill="#8b949e">YOUR_GITHUB_USERNAME@github: ~/portrait.sh</text>']
for y,line in enumerate(lines):
    parts.append(f'<text x="24" y="{58+y*4.7+3.8:.2f}" fill="#d7dee7" font-family="DejaVu Sans Mono, monospace" font-size="4.7" xml:space="preserve" textLength="812" lengthAdjust="spacingAndGlyphs">{html.escape(line)}</text>')
parts += ['<line x1="0" y1="890" x2="860" y2="890" stroke="#30363d"/>',
'<text x="24" y="913" font-family="monospace" font-size="11" fill="#8b949e">portrait generated from source-photo.png</text>','</svg>']
open(out,'w',encoding='utf-8').write('\\n'.join(parts))
print("Generated", out)
