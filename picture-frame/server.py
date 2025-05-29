from flask import Flask, request, send_from_directory, render_template_string, redirect
import os
import json

IMAGE_FOLDER = './imgs'
IMG_DESCR_FILE = 'img_descr.json'
MAX_IMAGES = 20

app = Flask(__name__)


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

HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Photo Frame</title>
  <style>
    body { font-family: sans-serif; }
    .drop-area {
      border: 2px dashed #888;
      padding: 20px;
      margin-bottom: 20px;
      text-align: center;
      color: #888;
    }
    .drop-area.dragover {
      border-color: #333;
      color: #333;
    }
    img { max-height: 100px; display: block; margin-bottom: 10px; }
    li { margin-bottom: 20px; }
  </style>
</head>
<body>
  <h2>Upload New Photo</h2>
  <div class="drop-area" id="drop-area">
    Drag & Drop Images Here
    <form id="upload-form" method="POST" enctype="multipart/form-data">
      <input type="file" name="files" id="fileElem" accept="image/*" multiple style="display:none" onchange="uploadFiles(this.files)">
    </form>
    <br><button onclick="document.getElementById('fileElem').click()">Browse Files</button>
  </div>

  {% if message %}<p style='color:red;'>{{ message }}</p>{% endif %}
  <hr>
  <h3>Files:</h3>
  <ol>
  {% for f in files %}
    <li>
      <img src="/imgs/{{ f }}"><br>
      {{ f }}<br>
      <form method="POST" action="/rename/{{ f }}">
        <input name="newname" value="{{ descriptions.get(f, '') }}">
        <input type="submit" value="Update Caption">
      </form>
      <a href="/delete/{{ f }}" onclick="return confirm('Are you sure you want to delete {{ f }}?')" style="color:red">(delete)</a>
    </li>
  {% endfor %}
  </ol>

<script>
function uploadFiles(files) {
  if (!files.length) return;
  const formData = new FormData();
  for (let file of files) {
    formData.append('files', file);
  }
  fetch('/', {
    method: 'POST',
    body: formData
  }).then(() => location.reload());
}

dropArea = document.getElementById('drop-area');
dropArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropArea.classList.add('dragover');
});
dropArea.addEventListener('dragleave', () => {
  dropArea.classList.remove('dragover');
});
dropArea.addEventListener('drop', (e) => {
  e.preventDefault();
  dropArea.classList.remove('dragover');
  uploadFiles(e.dataTransfer.files);
});
</script>
</body>
</html>
"""


@app.route('/', methods=['GET', 'POST'])
def index():
    global IMG_DESCR
    message = ""
    if request.method == 'POST':
        files = request.files.getlist('files')
        current_count = len(os.listdir(IMAGE_FOLDER))
        if current_count + len(files) > MAX_IMAGES:
            message = f"Image limit of {MAX_IMAGES} exceeded. Delete some images first."
        else:
            for file in files:
                if file:
                    file.save(os.path.join(IMAGE_FOLDER, file.filename))
            return redirect('/')
    files = sorted(os.listdir(IMAGE_FOLDER))
    return render_template_string(HTML, files=files, descriptions=IMG_DESCR, message=message)


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


@app.route('/imgs/<filename>')
def get_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)


def start_flask():
    app.run(host='0.0.0.0', port=8080)
