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

# --- CONFIG ---
IMAGE_FOLDER = './imgs'
DISPLAY_TIME = 1  # seconds
FADE_DURATION = 1.0  # seconds
FONT_SIZE = 50
SHUFFLE = True
LOOP = True
with open("img_descr.json") as f:
    IMG_DESCR = json.load(f)


# --- INIT PYGAME ---
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)
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
    caption = font.render(text, True, (255, 255, 255))
    bg = pygame.Surface((caption.get_width() + 20, caption.get_height() + 10))
    bg.set_alpha(150)
    bg.fill((0, 0, 0))
    screen.blit(bg, (10, screen_height - caption.get_height() - 20))
    screen.blit(caption, (20, screen_height - caption.get_height() - 15))

# --- FLASK REMOTE CONTROL ---
app = Flask(__name__)
remote_command = {"action": None, "paused": False}

@app.route("/next")
def next_image():
    remote_command["action"] = "next"
    return "Next image"

@app.route("/prev")
def prev_image():
    remote_command["action"] = "prev"
    return "Previous image"

@app.route("/pause")
def pause():
    remote_command["paused"] = True
    return "Paused"

@app.route("/resume")
def resume():
    remote_command["paused"] = False
    return "Resumed"

def start_server():
    app.run(host="0.0.0.0", port=8001)

Thread(target=start_server, daemon=True).start()

# --- MAIN LOOP ---
image_files = sorted(glob(os.path.join(IMAGE_FOLDER, '*')))
if SHUFFLE:
    random.shuffle(image_files)

idx = 0
running = True

while running:
    if idx >= len(image_files):
        if LOOP:
            image_files = sorted(glob(os.path.join(IMAGE_FOLDER, '*')))
            if SHUFFLE:
                random.shuffle(image_files)
            idx = 0
        else:
            break

    path = image_files[idx]
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

        if remote_command["paused"]:
            time.sleep(0.1)
            continue

        if remote_command["action"] == "next":
            idx = (idx + 1) % len(image_files)
            remote_command["action"] = None
            break
        elif remote_command["action"] == "prev":
            idx = (idx - 1) % len(image_files)
            remote_command["action"] = None
            break

        clock.tick(30)
    else:
        idx = (idx + 1) % len(image_files)

pygame.quit()
