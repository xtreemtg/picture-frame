from flask import Flask, request, send_from_directory, render_template, redirect
import os
import json

IMAGE_FOLDER = './static/imgs'
IMG_DESCR_FILE = 'img_descr.json'
MAX_IMAGES = 20

app = Flask(__name__, template_folder='templates', static_folder='static')


def load_img_descr():
    try:
        with open(IMG_DESCR_FILE) as f:
            return json.load(f)
    except:
        return {}


def save_img_descr(data):
    with open(IMG_DESCR_FILE, "w") as f:
        json.dump(data, f, indent=2)


IMG_DESCR = load_img_descr()


@app.route('/', methods=['GET'])
def index():
    global IMG_DESCR
    message = request.args.get('message', '')
    files = sorted(os.listdir(IMAGE_FOLDER))
    return render_template('index.html', files=files, descriptions=IMG_DESCR, message=message)
    # files = sorted(os.listdir(IMAGE_FOLDER))
    # return render_template_string(HTML, files=files, descriptions=IMG_DESCR, message=message)


@app.route('/delete/<filename>')
def delete(filename):
    global IMG_DESCR
    try:
        os.remove(os.path.join(IMAGE_FOLDER, filename))
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
    current_count = len(os.listdir(IMAGE_FOLDER))
    if current_count >= MAX_IMAGES or current_count + len(files) > MAX_IMAGES:
        return "Image limit exceeded", 400
    for file in files:
        if file:
            file.save(os.path.join(IMAGE_FOLDER, file.filename))
    return "OK"


@app.route('/imgs/<filename>')
def get_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)


def start_flask():
    app.run(host='0.0.0.0', port=8080)
