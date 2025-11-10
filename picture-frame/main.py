from pathlib import Path

import pygame
import json
import os
import time
import random
from glob import glob
from threading import Thread
from flask import Flask
from PIL import Image, ExifTags
from functools import lru_cache
from server import start_flask
import yaml

# --- CONFIG ---
with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)
    print(CONFIG)

IMAGE_FOLDER = CONFIG.get("IMAGE_FOLDER", "./static/imgs")
DISPLAY_TIME = CONFIG.get("DISPLAY_TIME", 1)
FADE_DURATION = CONFIG.get("FADE_DURATION", 1.0)
FONT_SIZE = CONFIG.get("FONT_SIZE", 50)
SHUFFLE = CONFIG.get("SHUFFLE", True)
LOOP = CONFIG.get("LOOP", True)

os.environ['SDL_VIDEO_WINDOW_POS'] = CONFIG.get("SDL_VIDEO_WINDOW_POS", "100,100")


# --- INIT IMAGE DESCRIPTIONS ---
def load_img_descr():
    try:
        with open("img_descr.json") as f:
            return json.load(f)
    except:
        return {}

def save_img_descr(data):
    with open("img_descr.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

IMG_DESCR = load_img_descr()


# --- INIT PYGAME ---
pygame.init()
pygame.display.set_caption("Xtreem Picture Frame")
window_width, window_height = CONFIG.get("WINDOW_WIDTH"), CONFIG.get("WINDOW_HEIGHT")
if not window_width and not window_height:
    display_info = pygame.display.Info()
    full_width = display_info.current_w
    full_height = display_info.current_h

    # Reduce dimensions slightly (e.g., 90% of full screen)
    margin_ratio = 0.9
    window_width = int(full_width * margin_ratio)
    window_height = int(full_height * margin_ratio)

# Set the window to be slightly smaller and resizable
screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)

# Now you can use these for layout
screen_width, screen_height = screen.get_size()

clock = pygame.time.Clock()
font = pygame.font.Font(None, FONT_SIZE)

# --- HELPER FUNCTIONS ---
def get_exif_rotation(img_path):
    try:
        image = Image.open(img_path)
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())
        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
        return pygame.image.fromstring(image.tobytes(), image.size, image.mode)
    except:
        return pygame.image.load(img_path)

def scale_image_aspect_fit(image, screen_size):
    image_rect = image.get_rect()
    screen_w, screen_h = screen_size
    image_w, image_h = image_rect.size

    ratio = min(screen_w / image_w, screen_h / image_h)
    new_size = (int(image_w * ratio), int(image_h * ratio))

    return pygame.transform.smoothscale(image, new_size)

@lru_cache(maxsize=2)
def load_image(path):
    try:
        img = get_exif_rotation(path)
        # return pygame.transform.scale(img, (screen_width, screen_height))
        return scale_image_aspect_fit(img, screen.get_size())
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def fade_in(image, duration=1.0, fps=30):
    for alpha in range(0, 256, int(255 / (duration * fps))):
        image.set_alpha(alpha)
        screen.fill((0, 0, 0))
        image_rect = image.get_rect(center=screen.get_rect().center)
        screen.blit(image, image_rect)
        # screen.blit(image, (0, 0))
        pygame.display.flip()
        clock.tick(fps)
    image.set_alpha(None)

def draw_caption(text):
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if font.size(test_line)[0] > screen_width - 40:
            lines.append(line)
            line = word
        else:
            line = test_line
    lines.append(line)

    total_height = len(lines) * (font.get_height() + 5)
    y = screen_height - total_height - 20

    for line in lines:
        caption = font.render(line, True, (255, 255, 255))
        bg = pygame.Surface((caption.get_width() + 20, caption.get_height() + 10))
        bg.set_alpha(150)
        bg.fill((0, 0, 0))
        screen.blit(bg, (10, y))
        screen.blit(caption, (20, y + 5))
        y += font.get_height() + 5


# --- MAIN LOOP ---
def scan_images():
    return sorted(Path(IMAGE_FOLDER).glob("*"))

image_files = scan_images()
if SHUFFLE:
    random.shuffle(image_files)

idx = 0
image_count = 0

running = True
Thread(target=start_flask, daemon=True).start()

while running:
    current_files = set(scan_images())
    if len(current_files) == 0:
        screen.fill((0, 0, 0)) # fill with black
        pygame.display.update()
        pygame.event.get()
        clock.tick(1)
        time.sleep(1)
        continue
    IMG_DESCR = load_img_descr()
    if current_files != set(image_files):
        added = current_files - set(image_files)
        removed = set(image_files) - current_files
        if added:
            print(f"New images added: {[f.name for f in added]}")
        if removed:
            print(f"Images removed: {[f.name for f in removed]}")
        image_files = sorted(current_files)
        if SHUFFLE:
            random.shuffle(image_files)
        if idx >= len(image_files):
            idx = 0

    # if idx >= len(image_files):
    #     if LOOP:
    #         idx = 0
    #     else:
    #         break

    path = str(image_files[idx])
    img = load_image(path)
    if not img:
        idx = (idx + 1) % len(image_files)
        continue

    fade_in(img, duration=FADE_DURATION)
    img_name = os.path.basename(path)
    desc = IMG_DESCR.get(img_name, img_name)
    draw_caption(desc)
    pygame.display.flip()

    start_time = time.time()
    while time.time() - start_time < DISPLAY_TIME:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
                break
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.size
        clock.tick(30)
    else:
        idx = (idx + 1) % len(image_files)

pygame.quit()
