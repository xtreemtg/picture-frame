from flask import Flask, request, send_from_directory, render_template, redirect
from PIL import Image, ImageOps
from werkzeug.utils import secure_filename
import exifread
import os
import json
import datetime
from dateutil import parser
import yaml



with open("config.yaml") as f:
    CONFIG = yaml.safe_load(f)

IMG_DESCR_FILE = CONFIG.get("IMG_DESCR_FILE", "img_descr.json")
IMAGE_FOLDER = CONFIG.get("IMAGE_FOLDER", "./static/imgs")
THUMB_FOLDER = CONFIG.get("THUMB_FOLDER", "./static/thumbnails")
MAX_IMAGES = CONFIG.get("MAX_IMAGES", 20)

os.makedirs(IMAGE_FOLDER, exist_ok=True)
os.makedirs(THUMB_FOLDER, exist_ok=True)

app = Flask(__name__, template_folder='templates', static_folder='static')


def load_img_descr():
    try:
        with open(IMG_DESCR_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_img_descr(data):
    with open(IMG_DESCR_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


IMG_DESCR = load_img_descr()


@app.route('/', methods=['GET'])
def index():
    global IMG_DESCR
    message = request.args.get('message', '')
    files = sorted(
        os.listdir(IMAGE_FOLDER),
        key=lambda fil: os.path.getmtime(os.path.join(IMAGE_FOLDER, fil)),
        reverse=True
    )
    dates = {
        f: datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(IMAGE_FOLDER, f))).strftime(
            '%Y-%m-%d %H:%M:%S')
        for f in files
    }

    return render_template('index.html', files=files, descriptions=IMG_DESCR, message=message,
                           dates=dates, max_images=MAX_IMAGES)
    # files = sorted(os.listdir(IMAGE_FOLDER))
    # return render_template_string(HTML, files=files, descriptions=IMG_DESCR, message=message)


@app.route('/delete/<filename>')
def delete(filename):
    global IMG_DESCR
    try:
        os.remove(os.path.join(IMAGE_FOLDER, filename))
        os.remove(os.path.join(THUMB_FOLDER, filename))
        IMG_DESCR.pop(filename, None)
        save_img_descr(IMG_DESCR)
    except:
        pass
    return redirect('/')


@app.route('/rename/<filename>', methods=['POST'])
def rename(filename):
    global IMG_DESCR
    newname = request.form.get('newname', '').strip()
    if newname:
        IMG_DESCR[filename] = newname
        save_img_descr(IMG_DESCR)
    return redirect('/')


@app.route('/upload', methods=['POST'])
def upload():
    global IMG_DESCR
    files = request.files.getlist('files')
    timestamps = request.form.get('timestamps')
    timestamps = json.loads(timestamps) if timestamps else {}
    current_count = len(os.listdir(IMAGE_FOLDER))
    if current_count >= MAX_IMAGES or current_count + len(files) > MAX_IMAGES:
        return "Image limit exceeded", 400
    for file in files:
        if file:
            filename = file.filename
            print(f"Uploading {filename}")
            original_path = os.path.join(IMAGE_FOLDER, filename)
            file.save(original_path)
            with open(original_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
            exif_datetime_str = tags.get('Image DateTime')
            ts = None
            if exif_datetime_str:
                try:
                    exif_dt = datetime.datetime.strptime(str(exif_datetime_str), '%Y:%m:%d %H:%M:%S')
                    ts = exif_dt.timestamp()
                except (ValueError, TypeError):
                    try:
                        exif_dt = parser.parse(str(exif_datetime_str))
                        ts = exif_dt.timestamp()
                    except (ValueError, TypeError):
                        pass
            if ts is None and file.filename in timestamps:
                ts = int(timestamps[file.filename]) / 1000

            if ts is not None:
                os.utime(original_path, (ts, ts))
            thumb_path = os.path.join(THUMB_FOLDER, file.filename)
            with Image.open(original_path) as img:
                img = ImageOps.exif_transpose(img)
                img.thumbnail((400, 400))
                img.save(thumb_path)
    return "OK"


@app.route('/imgs/<filename>')
def get_image(filename):
    return send_from_directory(THUMB_FOLDER, filename)


def start_flask():
    app.run(host='0.0.0.0', port=8080)
