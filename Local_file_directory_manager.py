from flask import Flask, render_template_string, send_from_directory, request, redirect
import os

app = Flask(__name__)

ROOT_DIR = r"C:\shared_folder"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8">

<title>Local File Manager</title>

<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

<style>

body{
background:#f4f6f9;
color:#000;
transition:0.3s;
}

.dark-mode{
background:#121212;
color:#e4e4e4;
}

.container-box{
max-width:900px;
margin:auto;
margin-top:40px;
}

.file-card{
padding:12px;
border-radius:12px;
margin-bottom:8px;
background:white;
box-shadow:0 2px 6px rgba(0,0,0,0.08);
transition:0.2s;
display:flex;
justify-content:space-between;
}

.dark-mode .file-card{
background:#1e1e1e;
}

.file-card:hover{
transform:scale(1.02);
}

.upload-box{
background:white;
padding:20px;
border-radius:15px;
box-shadow:0 4px 10px rgba(0,0,0,0.1);
margin-bottom:25px;
}

.dark-mode .upload-box{
background:#1e1e1e;
}

</style>

</head>

<body>

<div class="container-box">

<div class="d-flex justify-content-between align-items-center mb-4">

<h2>📂 Local File Manager</h2>

<button class="btn btn-outline-secondary" onclick="toggleDark()">Dark Mode</button>

</div>


<div class="upload-box">

<form method="POST" action="/upload/{{path}}" enctype="multipart/form-data">

<div class="input-group">

<input class="form-control" type="file" name="file">

<button class="btn btn-primary">Upload</button>

</div>

</form>

</div>


{% if path %}
<a class="btn btn-secondary mb-3" href="/browse/{{parent}}">⬅ Back</a>
{% endif %}


{% for folder in folders %}

<div class="file-card">

<div>
📁 <a href="/browse/{{folder}}" class="text-decoration-none">
{{folder.split('/')[-1]}}
</a>
</div>

<div>Folder</div>

</div>

{% endfor %}


{% for file in files %}

<div class="file-card">

<div>
📄 <a href="/download/{{file.path}}" class="text-decoration-none">
{{file.name}}
</a>
</div>

<div class="text-muted">
{{file.size}}
</div>

</div>

{% endfor %}

</div>


<script>

function toggleDark(){

document.body.classList.toggle("dark-mode")

}

</script>

</body>
</html>

"""

def format_size(size):
    for unit in ['B','KB','MB','GB','TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024



@app.route("/")
def index():
    return browse("")


@app.route("/browse/")
@app.route("/browse/<path:subpath>")
def browse(subpath=""):

    path = os.path.join(ROOT_DIR, subpath)

    folders = []
    files = []

    for item in os.listdir(path):

        full = os.path.join(path, item)

        if os.path.isdir(full):
            folders.append(os.path.join(subpath, item).replace("\\","/"))

        else:
            size = os.path.getsize(full)

            files.append({
                "name": item,
                "path": os.path.join(subpath, item).replace("\\","/"),
                "size": format_size(size)
            })

    parent = "/".join(subpath.split("/")[:-1])

    return render_template_string(
        TEMPLATE,
        folders=folders,
        files=files,
        path=subpath,
        parent=parent
    )


@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(ROOT_DIR, filename, as_attachment=True)


@app.route("/upload/<path:subpath>", methods=["POST"])
def upload(subpath):

    file = request.files["file"]

    if file.filename == "":
        return redirect(request.referrer)

    save_path = os.path.join(ROOT_DIR, subpath, file.filename)

    file.save(save_path)

    return redirect("/browse/" + subpath)


@app.route("/upload/", methods=["POST"])
def upload_root():

    file = request.files["file"]

    save_path = os.path.join(ROOT_DIR, file.filename)

    file.save(save_path)

    return redirect("/")


app.run(host="0.0.0.0", port=5000)
