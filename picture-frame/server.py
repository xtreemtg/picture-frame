from flask import Flask, request, send_from_directory, render_template_string, redirect
import os

UPLOAD_FOLDER = './imgs'
app = Flask(__name__)

HTML = """
<h2>Upload New Photo</h2>
<form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" required>
    <input type="submit" value="Upload">
</form>
<hr>
<h3>Files:</h3>
<ul>
{% for f in files %}
  <li>{{ f }} 
      <a href="/delete/{{ f }}" style="color:red">(delete)</a>
  </li>
{% endfor %}
</ul>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            return redirect('/')
    files = sorted(os.listdir(UPLOAD_FOLDER))
    return render_template_string(HTML, files=files)

@app.route('/delete/<filename>')
def delete(filename):
    try:
        os.remove(os.path.join(UPLOAD_FOLDER, filename))
    except:
        pass
    return redirect('/')

@app.route('/imgs/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
