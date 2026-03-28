#!/usr/bin/env python3
"""
Generate Google Play Store screenshots with modern phone frames
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Google Play dimensions: 1080x1920 (portrait phone)
CANVAS_W = 1080
CANVAS_H = 1920

# Phone frame dimensions
PHONE_W = 780
PHONE_H = 1580
SCREEN_W = 720
SCREEN_H = 1460
CORNER_R = 50
PHONE_CORNER_R = 58
NOTCH_W = 200
NOTCH_H = 28

# Colors
BG_DARK = (12, 12, 16)
ACCENT = (225, 255, 1)  # IngresoQR yellow-green
WHITE = (255, 255, 255)
GRAY = (140, 140, 145)
PHONE_BORDER = (50, 50, 55)
PHONE_BG = (25, 25, 30)

def load_font(size, bold=False):
    """Try to load a good font, fallback to default"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def create_phone_frame(screenshot_path, title, subtitle, output_path):
    """Create a Google Play screenshot with phone frame"""
    
    # Create canvas
    img = Image.new('RGB', (CANVAS_W, CANVAS_H), BG_DARK)
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    title_font = load_font(52, bold=True)
    subtitle_font = load_font(28)
    
    # Draw title text at top
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = (CANVAS_W - title_w) // 2
    draw.text((title_x, 60), title, fill=WHITE, font=title_font)
    
    # Draw subtitle
    sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (CANVAS_W - sub_w) // 2
    draw.text((sub_x, 130), subtitle, fill=GRAY, font=subtitle_font)
    
    # Draw accent line under title
    line_w = 80
    line_x = (CANVAS_W - line_w) // 2
    draw.rounded_rectangle(
        (line_x, 175, line_x + line_w, 179),
        radius=2, fill=ACCENT
    )
    
    # Phone position
    phone_x = (CANVAS_W - PHONE_W) // 2
    phone_y = 220
    
    # Draw phone shadow (subtle)
    for i in range(20, 0, -1):
        alpha = 3
        shadow_color = (0, 0, 0)
        draw.rounded_rectangle(
            (phone_x - i, phone_y + i, phone_x + PHONE_W + i, phone_y + PHONE_H + i),
            radius=PHONE_CORNER_R + i,
            fill=shadow_color
        )
    
    # Draw phone body
    draw.rounded_rectangle(
        (phone_x, phone_y, phone_x + PHONE_W, phone_y + PHONE_H),
        radius=PHONE_CORNER_R, fill=PHONE_BG, outline=PHONE_BORDER, width=3
    )
    
    # Draw screen area (slightly inset)
    screen_x = phone_x + (PHONE_W - SCREEN_W) // 2
    screen_y = phone_y + (PHONE_H - SCREEN_H) // 2
    
    # Draw screen background
    draw.rounded_rectangle(
        (screen_x, screen_y, screen_x + SCREEN_W, screen_y + SCREEN_H),
        radius=CORNER_R, fill=(20, 20, 24)
    )
    
    # Load and paste screenshot
    if os.path.exists(screenshot_path):
        screenshot = Image.open(screenshot_path)
        # Resize to fit screen area
        screenshot = screenshot.resize((SCREEN_W, SCREEN_H), Image.LANCZOS)
        
        # Create rounded mask
        mask = Image.new('L', (SCREEN_W, SCREEN_H), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            (0, 0, SCREEN_W, SCREEN_H),
            radius=CORNER_R, fill=255
        )
        
        img.paste(screenshot, (screen_x, screen_y), mask)
    
    # Draw notch at top of screen
    notch_x = phone_x + (PHONE_W - NOTCH_W) // 2
    notch_y = screen_y
    draw.rounded_rectangle(
        (notch_x, notch_y, notch_x + NOTCH_W, notch_y + NOTCH_H),
        radius=14, fill=(12, 12, 16)
    )
    
    # Small camera dot in notch
    cam_x = phone_x + PHONE_W // 2
    cam_y = notch_y + NOTCH_H // 2
    draw.ellipse((cam_x - 5, cam_y - 5, cam_x + 5, cam_y + 5), fill=(40, 40, 45))
    
    # Bottom bar indicator
    bar_w = 160
    bar_x = phone_x + (PHONE_W - bar_w) // 2
    bar_y = phone_y + PHONE_H - 25
    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + bar_w, bar_y + 5),
        radius=3, fill=GRAY
    )
    
    # Draw small IngresoQR branding at bottom
    brand_font = load_font(22, bold=True)
    brand_text = "IngresoQR"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=brand_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    brand_x = (CANVAS_W - brand_w) // 2
    
    # Accent dot before text
    draw.ellipse((brand_x - 20, CANVAS_H - 55, brand_x - 10, CANVAS_H - 45), fill=ACCENT)
    draw.text((brand_x, CANVAS_H - 60), brand_text, fill=GRAY, font=brand_font)
    
    img.save(output_path, quality=95)
    print(f"  Created: {output_path}")


# Screenshots config: (file, title, subtitle)
screenshots = [
    ("00_login.png", "Acceso Rapido", "Ingresa con tu codigo de socio"),
    ("01_home_qr.png", "Tu QR Dinamico", "Accede al gimnasio al instante"),
    ("02_classes.png", "Reserva Clases", "Consulta horarios y reserva tu lugar"),
    ("03_history.png", "Historial de Accesos", "Registro detallado de entradas y salidas"),
    ("05_membership.png", "Tu Membresia", "Gestiona tu plan y pagos facilmente"),
    ("06_notifications.png", "Notificaciones", "Mantente informado de las novedades"),
    ("07_profile.png", "Tu Perfil", "Toda tu informacion en un solo lugar"),
    ("08_achievements.png", "Logros y Rachas", "Gana puntos con cada visita"),
]

output_dir = "/app/docs/google_play_screenshots"
os.makedirs(output_dir, exist_ok=True)

for i, (filename, title, subtitle) in enumerate(screenshots):
    src = f"/app/screenshots/{filename}"
    dst = f"{output_dir}/{i+1:02d}_{filename.replace('.png', '_framed.png')}"
    if os.path.exists(src):
        create_phone_frame(src, title, subtitle, dst)
    else:
        print(f"  SKIP: {src} not found")

print(f"\nDone! {len(screenshots)} screenshots generated in {output_dir}")
