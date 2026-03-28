#!/usr/bin/env python3
"""
Generate Google Play Feature Graphic (1024x500px)
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1024, 500

def load_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

img = Image.new('RGB', (W, H), (10, 10, 14))
draw = ImageDraw.Draw(img)

# Subtle grid pattern
for x in range(0, W, 40):
    draw.line([(x, 0), (x, H)], fill=(18, 18, 22), width=1)
for y in range(0, H, 40):
    draw.line([(0, y), (W, y)], fill=(18, 18, 22), width=1)

# Accent glow circle (bottom left, subtle)
for r in range(200, 0, -1):
    alpha = max(0, int(12 * (1 - r/200)))
    color = (int(225 * alpha/12), int(255 * alpha/12), int(1 * alpha/12))
    draw.ellipse([80-r, H-100-r, 80+r, H-100+r], fill=color)

# Accent glow (top right, subtle)
for r in range(150, 0, -1):
    alpha = max(0, int(8 * (1 - r/150)))
    color = (int(225 * alpha/8), int(255 * alpha/8), int(1 * alpha/8))
    draw.ellipse([W-150-r, 50-r, W-150+r, 50+r], fill=color)

# Phone mockup (simplified, right side)
phone_x, phone_y = 700, 30
phone_w, phone_h = 220, 440
phone_r = 28

# Phone shadow
for i in range(15, 0, -1):
    draw.rounded_rectangle(
        [phone_x-i, phone_y+i+2, phone_x+phone_w+i, phone_y+phone_h+i+2],
        radius=phone_r+i, fill=(0, 0, 0)
    )

# Phone body
draw.rounded_rectangle(
    [phone_x, phone_y, phone_x+phone_w, phone_y+phone_h],
    radius=phone_r, fill=(22, 22, 26), outline=(50, 50, 55), width=2
)

# Phone screen
scr_margin = 8
scr_x1 = phone_x + scr_margin
scr_y1 = phone_y + scr_margin + 15
scr_x2 = phone_x + phone_w - scr_margin
scr_y2 = phone_y + phone_h - scr_margin - 15
draw.rounded_rectangle(
    [scr_x1, scr_y1, scr_x2, scr_y2],
    radius=18, fill=(16, 16, 20)
)

# QR code simulation inside phone
qr_size = 120
qr_x = scr_x1 + (scr_x2 - scr_x1 - qr_size) // 2
qr_y = scr_y1 + 60

# White QR background
draw.rounded_rectangle(
    [qr_x - 8, qr_y - 8, qr_x + qr_size + 8, qr_y + qr_size + 8],
    radius=8, fill=(255, 255, 255)
)

# QR pattern (realistic looking)
import random
random.seed(42)
cell = 6
for row in range(qr_size // cell):
    for col in range(qr_size // cell):
        # Corner patterns (always filled)
        is_corner = (
            (row < 4 and col < 4) or
            (row < 4 and col >= qr_size//cell - 4) or
            (row >= qr_size//cell - 4 and col < 4)
        )
        if is_corner or random.random() > 0.5:
            draw.rectangle(
                [qr_x + col*cell, qr_y + row*cell,
                 qr_x + col*cell + cell-1, qr_y + row*cell + cell-1],
                fill=(10, 10, 14)
            )

# Accent ring around QR
ring_cx = qr_x + qr_size // 2
ring_cy = qr_y + qr_size // 2
ring_r = qr_size // 2 + 20
draw.arc(
    [ring_cx - ring_r, ring_cy - ring_r, ring_cx + ring_r, ring_cy + ring_r],
    start=-60, end=240, fill=(225, 255, 1), width=3
)

# Member name in phone
name_font = load_font(13, bold=True)
name_text = "Carlos M."
nb = draw.textbbox((0,0), name_text, font=name_font)
name_w = nb[2] - nb[0]
draw.text((scr_x1 + (scr_x2-scr_x1-name_w)//2, scr_y1 + 25), name_text, fill=(255,255,255), font=name_font)

# Code under name
code_font = load_font(10)
code_text = "NT879K"
cb = draw.textbbox((0,0), code_text, font=code_font)
code_w = cb[2] - cb[0]
draw.text((scr_x1 + (scr_x2-scr_x1-code_w)//2, scr_y1 + 43), code_text, fill=(140,140,145), font=code_font)

# Membership bar in phone
bar_y = qr_y + qr_size + 30
bar_x1 = scr_x1 + 12
bar_x2 = scr_x2 - 12
draw.rounded_rectangle([bar_x1, bar_y, bar_x2, bar_y + 30], radius=8, fill=(28, 28, 32))
mem_font = load_font(9)
draw.text((bar_x1 + 10, bar_y + 5), "Membresia", fill=(140,140,145), font=mem_font)
mem_bold = load_font(10, bold=True)
draw.text((bar_x1 + 10, bar_y + 16), "30 dias", fill=(255,255,255), font=mem_bold)

# Bottom nav in phone
nav_y = scr_y2 - 28
draw.line([(scr_x1+10, nav_y), (scr_x2-10, nav_y)], fill=(35,35,40), width=1)
nav_items = ["QR", "Clases", "Avisos", "Perfil"]
nav_font = load_font(8)
nav_w = (scr_x2 - scr_x1) // len(nav_items)
for i, item in enumerate(nav_items):
    ib = draw.textbbox((0,0), item, font=nav_font)
    iw = ib[2] - ib[0]
    ix = scr_x1 + i * nav_w + (nav_w - iw) // 2
    color = (225, 255, 1) if i == 0 else (100, 100, 105)
    draw.text((ix, nav_y + 8), item, fill=color, font=nav_font)

# Notch
notch_w = 60
notch_x = phone_x + (phone_w - notch_w) // 2
draw.rounded_rectangle([notch_x, phone_y + 2, notch_x + notch_w, phone_y + 14], radius=7, fill=(10, 10, 14))

# Home bar
hb_w = 80
hb_x = phone_x + (phone_w - hb_w) // 2
draw.rounded_rectangle([hb_x, phone_y + phone_h - 12, hb_x + hb_w, phone_y + phone_h - 8], radius=3, fill=(80,80,85))

# ========== LEFT SIDE TEXT ==========

# Main title: IngresoQR
title_font = load_font(62, bold=True)
draw.text((60, 100), "IngresoQR", fill=(255, 255, 255), font=title_font)

# Accent underline
draw.rounded_rectangle([60, 175, 160, 180], radius=2, fill=(225, 255, 1))

# Subtitle
sub_font = load_font(22)
draw.text((60, 200), "Control de acceso inteligente", fill=(180, 180, 185), font=sub_font)
draw.text((60, 230), "para tu gimnasio", fill=(180, 180, 185), font=sub_font)

# Feature pills
pill_font = load_font(13, bold=True)
pills = ["QR Dinamico", "Reservas", "Pagos", "Estadisticas"]
px = 60
py = 290

for pill_text in pills:
    pb = draw.textbbox((0,0), pill_text, font=pill_font)
    pw = pb[2] - pb[0] + 24
    ph = 32
    # Pill background
    draw.rounded_rectangle([px, py, px+pw, py+ph], radius=16, fill=(225, 255, 1))
    draw.text((px + 12, py + 7), pill_text, fill=(10, 10, 14), font=pill_font)
    px += pw + 10

# Second row of pills
px = 60
py = 332
pills2 = ["Clases", "Logros", "Notificaciones"]
for pill_text in pills2:
    pb = draw.textbbox((0,0), pill_text, font=pill_font)
    pw = pb[2] - pb[0] + 24
    ph = 32
    draw.rounded_rectangle([px, py, px+pw, py+ph], radius=16, outline=(225, 255, 1), width=2)
    draw.text((px + 12, py + 7), pill_text, fill=(225, 255, 1), font=pill_font)
    px += pw + 10

# Bottom tagline
tag_font = load_font(14)
draw.text((60, H - 60), "Tu acceso al gym, en un toque", fill=(100, 100, 105), font=tag_font)

# Small dot accent
draw.ellipse([45, H-55, 53, H-47], fill=(225, 255, 1))

# Save
output_path = "/app/docs/google_play_screenshots/feature_graphic_1024x500.png"
img.save(output_path, "PNG", optimize=True)
size_kb = os.path.getsize(output_path) / 1024
print(f"Created: {output_path}")
print(f"Size: {size_kb:.0f} KB ({W}x{H})")
