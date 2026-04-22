#!/usr/bin/env python3
"""
Create App Store screenshots with iPhone frame for IngresoQR.
Target: iPhone 15 Pro Max = 1284 x 2778 px
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

INPUT_DIR = "/app/frontend/public/play_screenshots"
OUTPUT_DIR = "/app/appstore_screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Target App Store size for iPhone 15 Pro Max
TARGET_W = 1284
TARGET_H = 2778

# iPhone frame dimensions (relative to target)
FRAME_PADDING_TOP = 130
FRAME_PADDING_BOTTOM = 130
FRAME_PADDING_SIDE = 42
CORNER_RADIUS = 60
NOTCH_WIDTH = 200
NOTCH_HEIGHT = 38
SCREEN_CORNER = 50

# Colors
BG_COLOR = (9, 9, 11)  # #09090B - app dark background
FRAME_COLOR = (30, 30, 34)  # Dark titanium
SCREEN_BG = (9, 9, 11)

def create_rounded_rectangle(size, radius, color):
    """Create an image with rounded rectangle."""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, size[0]-1, size[1]-1], radius=radius, fill=color)
    return img

def create_iphone_frame(screenshot_path, output_path, title=None):
    """Frame a screenshot in an iPhone mockup."""
    # Load screenshot
    screenshot = Image.open(screenshot_path).convert('RGBA')
    
    # Create canvas
    canvas = Image.new('RGBA', (TARGET_W, TARGET_H), BG_COLOR)
    draw = ImageDraw.Draw(canvas)
    
    # Phone frame area
    phone_x = FRAME_PADDING_SIDE
    phone_y = FRAME_PADDING_TOP
    phone_w = TARGET_W - 2 * FRAME_PADDING_SIDE
    phone_h = TARGET_H - FRAME_PADDING_TOP - FRAME_PADDING_BOTTOM
    
    # Draw phone body (rounded rectangle)
    phone_frame = create_rounded_rectangle((phone_w, phone_h), CORNER_RADIUS, FRAME_COLOR)
    canvas.paste(phone_frame, (phone_x, phone_y), phone_frame)
    
    # Screen area (inside the frame with bezels)
    bezel = 12
    screen_x = phone_x + bezel
    screen_y = phone_y + bezel
    screen_w = phone_w - 2 * bezel
    screen_h = phone_h - 2 * bezel
    
    # Draw screen background
    screen_bg = create_rounded_rectangle((screen_w, screen_h), SCREEN_CORNER, SCREEN_BG)
    canvas.paste(screen_bg, (screen_x, screen_y), screen_bg)
    
    # Resize screenshot to fit screen
    screenshot_resized = screenshot.resize((screen_w, screen_h), Image.LANCZOS)
    
    # Create rounded mask for screen
    mask = Image.new('L', (screen_w, screen_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, screen_w-1, screen_h-1], radius=SCREEN_CORNER, fill=255)
    
    canvas.paste(screenshot_resized, (screen_x, screen_y), mask)
    
    # Dynamic Island (notch)
    island_w = 180
    island_h = 48
    island_x = TARGET_W // 2 - island_w // 2
    island_y = phone_y + bezel + 12
    island_shape = create_rounded_rectangle((island_w, island_h), 24, (0, 0, 0, 255))
    canvas.paste(island_shape, (island_x, island_y), island_shape)
    
    # Side button (right side)
    btn_x = phone_x + phone_w - 1
    btn_y = phone_y + 280
    btn_h = 90
    draw.rectangle([btn_x, btn_y, btn_x + 3, btn_y + btn_h], fill=(45, 45, 50))
    
    # Volume buttons (left side)
    vol_x = phone_x - 3
    draw.rectangle([vol_x, phone_y + 240, vol_x + 3, phone_y + 290], fill=(45, 45, 50))
    draw.rectangle([vol_x, phone_y + 310, vol_x + 3, phone_y + 380], fill=(45, 45, 50))
    draw.rectangle([vol_x, phone_y + 400, vol_x + 3, phone_y + 470], fill=(45, 45, 50))
    
    # Convert to RGB
    final = Image.new('RGB', (TARGET_W, TARGET_H), BG_COLOR)
    final.paste(canvas, (0, 0), canvas)
    
    final.save(output_path, 'PNG', quality=100)
    print(f"Created: {output_path} ({TARGET_W}x{TARGET_H})")

# Process all screenshots
screenshots = {
    "01_00_login_framed.png": "01_login_framed",
    "02_01_home_qr_framed.png": "02_home_qr_framed",
    "03_02_classes_framed.png": "03_classes_framed",
    "04_03_history_framed.png": "04_history_framed",
    "05_05_membership_framed.png": "05_membership_framed",
    "06_06_notifications_framed.png": "06_notifications_framed",
    "07_07_profile_framed.png": "07_profile_framed",
    "08_08_achievements_framed.png": "08_achievements_framed",
}

for input_file, output_name in screenshots.items():
    input_path = os.path.join(INPUT_DIR, input_file)
    if os.path.exists(input_path):
        output_path = os.path.join(OUTPUT_DIR, f"{output_name}.png")
        create_iphone_frame(input_path, output_path)
    else:
        print(f"SKIP: {input_file} not found")

print(f"\nDone! {len(os.listdir(OUTPUT_DIR))} screenshots created in {OUTPUT_DIR}")
