from PIL import Image, ImageOps
import os


def generate_thumbnails(img_dir, thumb_dir):
    os.makedirs(thumb_dir, exist_ok=True)
    os.makedirs(img_dir, exist_ok=True)
    files = [f for f in os.listdir(img_dir) if not f.startswith('.')]
    for filename in files:
        original_path = os.path.join(img_dir, filename)
        thumb_path = os.path.join(thumb_dir, filename)
        if os.path.exists(original_path) and not os.path.exists(thumb_path):
            with Image.open(original_path) as img:
                img = ImageOps.exif_transpose(img)
                img.thumbnail((400, 400))
                img.save(thumb_path)
