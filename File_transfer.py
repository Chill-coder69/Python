from flask import Flask, request, send_from_directory, render_template_string
import os
import ctypes
import time

# once you run this in your system then you can upload file from any device to the device this script is running on
# NOTE : Make sure that both the device are connected to same local network
# NOTE : upload only small file (<5GB) or it may cause python to crash

time.sleep(1)
# Minimize current console window
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)
app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>File Transfer</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg, #1e1e2f, #2c2c3e);
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    margin: 0;
}

.container {
    background: #ffffff;
    width: 420px;
    padding: 30px;
    border-radius: 20px;
    box-shadow: 0 15px 40px rgba(0,0,0,0.3);
}

h2 {
    text-align: center;
}

input[type="file"] {
    width: 100%;
    margin: 15px 0;
}

button {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 15px;
    background: #4CAF50;
    color: white;
    font-size: 16px;
    cursor: pointer;
    transition: 0.3s;
}

button:hover {
    background: #45a049;
}

.progress-container {
    margin-top: 15px;
    background: #eee;
    border-radius: 15px;
    overflow: hidden;
    height: 20px;
    display: none;
}

.progress-bar {
    height: 100%;
    width: 0%;
    background: #4CAF50;
    transition: width 0.2s;
}

ul {
    list-style: none;
    padding: 0;
    margin-top: 20px;
}

li {
    margin: 8px 0;
}

a {
    text-decoration: none;
    color: #333;
    padding: 8px 12px;
    border-radius: 10px;
    background: #f2f2f2;
    display: inline-block;
}
.select-btn {
    width: 100%;
    padding: 12px;
    border: none;
    border-radius: 15px;
    background: #3b82f6;
    color: white;
    font-size: 16px;
    cursor: pointer;
    transition: 0.3s;
    margin-bottom: 10px;
}

.select-btn:hover {
    background: #2563eb;
    transform: scale(1.03);
}
</style>
</head>
<body>

<div class="container">
    <h2>Upload File</h2>

<input type="file" id="fileInput" hidden>

<button type="button" class="select-btn" onclick="document.getElementById('fileInput').click()">
    Select File
</button>

<div id="fileName" style="margin-top:10px; font-size:14px; color:#555;">
    No file selected
</div>

<button onclick="uploadFile()">Upload</button>
    <div class="progress-container" id="progressContainer">
        <div class="progress-bar" id="progressBar"></div>
    </div>

    <h2>Recent Files</h2>
    <ul>
    {% for file in files %}
        <li><a href="/download/{{file}}">{{file}}</a></li>
    {% endfor %}
    </ul>
</div>

<script>
function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/", true);

    const progressContainer = document.getElementById("progressContainer");
    const progressBar = document.getElementById("progressBar");
    progressContainer.style.display = "block";

    xhr.upload.onprogress = function(event) {
        if (event.lengthComputable) {
            const percent = (event.loaded / event.total) * 100;
            progressBar.style.width = percent + "%";
        }
    };

    xhr.onload = function() {
        if (xhr.status === 200) {
            progressBar.style.width = "100%";
            setTimeout(() => location.reload(), 800);
        }
    };

    xhr.send(formData);
}
document.getElementById("fileInput").addEventListener("change", function() {
    const fileName = this.files.length > 0 ? this.files[0].name : "No file selected";
    document.getElementById("fileName").innerText = fileName;
});
</script>

</body>
</html>
"""
@app.route("/", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["file"]
        if file:
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    files = os.listdir(UPLOAD_FOLDER)
    return render_template_string(HTML, files=files)

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

