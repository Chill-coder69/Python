"""
Remote script runner for Windows 10.

Setup:
    pip install flask waitress mss pillow
    python script_runner.py

On first start a random token is written to token.txt next to this file.
Open http://<this-pc-ip>:8765 from another device and paste the token.
Drop scripts into the "scripts" folder (or upload them from the page).
"""
import os
import subprocess
import sys
import threading
import time
import secrets
import codecs
import hmac
import io
import uuid
import ctypes
from functools import wraps
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

# Make screenshots use real pixels on scaled displays (125%, 150%...)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

PORT = 8765
BASE = Path(__file__).parent.resolve()
SCRIPTS = BASE / "scripts"
SCRIPTS.mkdir(exist_ok=True)

TOKEN_FILE = BASE / "token.txt"
if not TOKEN_FILE.exists():
    TOKEN_FILE.write_text(secrets.token_urlsafe(32))
TOKEN = TOKEN_FILE.read_text().strip()

# Only these extensions can be run or uploaded. Add more if you need them.
RUNNERS = {
    ".py": [sys.executable, "-u"],
    ".bat": ["cmd.exe", "/c"],
    ".cmd": ["cmd.exe", "/c"],
    ".ps1": ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"],
    ".js": ["node"],
    ".vbs": ["cscript.exe", "//nologo"],
}

NO_WINDOW = subprocess.CREATE_NO_WINDOW  # hides the console flash, GUI windows still show
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

JOBS = {}
LOCK = threading.Lock()


class Job:
    def __init__(self, name, proc):
        self.id = uuid.uuid4().hex[:8]
        self.name = name
        self.proc = proc
        self.started = time.time()
        self.out = ""  # everything the script printed (and what you typed), last 200 KB
        self.lock = threading.Lock()
        self.stopped = False  # set when the user presses Stop

    def add(self, text):
        with self.lock:
            self.out = (self.out + text)[-200_000:]

    def info(self):
        code = self.proc.poll()
        return {
            "id": self.id,
            "name": self.name,
            "running": code is None,
            "stopped": self.stopped,
            "exit_code": code,
            "started": time.strftime("%H:%M:%S", time.localtime(self.started)),
        }


def require_token(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        supplied = request.headers.get("X-Token", "")
        if not hmac.compare_digest(supplied, TOKEN):
            time.sleep(1)  # slows down guessing
            return jsonify(error="unauthorized"), 401
        return fn(*a, **kw)
    return wrapper


def resolve_script(name):
    """Accept only a bare filename that exists inside SCRIPTS."""
    path = (SCRIPTS / Path(name).name).resolve()
    if path.parent != SCRIPTS or not path.is_file() or path.suffix.lower() not in RUNNERS:
        return None
    return path


def pump_output(job):
    # Read raw chunks, not lines, so prompts like "Name: " show up before Enter is pressed
    dec = codecs.getincrementaldecoder("utf-8")(errors="replace")
    while True:
        chunk = job.proc.stdout.read1(4096)
        if not chunk:
            break
        job.add(dec.decode(chunk).replace("\r\n", "\n"))
    job.proc.stdout.close()


@app.get("/")
def index():
    return PAGE


@app.get("/api/scripts")
@require_token
def list_scripts():
    files = sorted(p.name for p in SCRIPTS.iterdir()
                   if p.is_file() and p.suffix.lower() in RUNNERS)
    return jsonify(files)


@app.post("/api/run")
@require_token
def run():
    path = resolve_script((request.get_json(silent=True) or {}).get("name", ""))
    if not path:
        return jsonify(error="no such script"), 404
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen(
        RUNNERS[path.suffix.lower()] + [str(path)],
        cwd=str(SCRIPTS),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
        creationflags=NO_WINDOW,
    )
    job = Job(path.name, proc)
    with LOCK:
        JOBS[job.id] = job
    threading.Thread(target=pump_output, args=(job,), daemon=True).start()
    return jsonify(job.info())


@app.get("/api/jobs")
@require_token
def jobs():
    with LOCK:
        items = [j.info() for j in JOBS.values()]
    return jsonify(sorted(items, key=lambda j: j["started"], reverse=True))


@app.get("/api/jobs/<job_id>")
@require_token
def job_output(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify(error="unknown job"), 404
    return jsonify(info=job.info(), output=job.out)


@app.post("/api/jobs/<job_id>/input")
@require_token
def send_input(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify(error="unknown job"), 404
    if job.proc.poll() is not None:
        return jsonify(error="That script has already ended."), 409
    text = str((request.get_json(silent=True) or {}).get("text", ""))[:4000]
    try:
        job.proc.stdin.write((text + "\n").encode("utf-8"))
        job.proc.stdin.flush()
    except (OSError, ValueError):
        return jsonify(error="The script isn't accepting input."), 409
    job.add(text + "\n")  # piped input isn't echoed by Windows, so show it ourselves
    return jsonify(ok=True)


@app.post("/api/jobs/<job_id>/stop")
@require_token
def stop(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify(error="unknown job"), 404
    if job.proc.poll() is None:
        job.stopped = True
        # /T kills the whole process tree, /F forces it
        subprocess.run(["taskkill", "/PID", str(job.proc.pid), "/T", "/F"],
                       capture_output=True, creationflags=NO_WINDOW)
    return jsonify(job.info())


@app.get("/api/screenshot")
@require_token
def screenshot():
    import mss
    from PIL import Image
    try:
        mon = int(request.args.get("monitor", 1))  # 1 = primary, 0 = all screens
    except ValueError:
        mon = 1
    try:
        with mss.mss() as sct:  # create per request: mss handles are per-thread
            if not 0 <= mon < len(sct.monitors):
                mon = 1
            shot = sct.grab(sct.monitors[mon])
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    except Exception as e:
        return jsonify(error=f"capture failed: {e}"), 500
    if img.width > 1600:  # keep transfers fast
        img = img.resize((1600, round(img.height * 1600 / img.width)))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=70)
    buf.seek(0)
    resp = send_file(buf, mimetype="image/jpeg")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.post("/api/upload")
@require_token
def upload():
    f = request.files.get("file")
    name = secure_filename(f.filename) if f else ""
    if not name or Path(name).suffix.lower() not in RUNNERS:
        return jsonify(error="file type not allowed"), 400
    f.save(SCRIPTS / name)
    return jsonify(saved=name)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Script Runner</title>
<style>
:root{--bg:#1a090d;--rail:#210d12;--panel:#2a1118;--line:#472029;--tx:#f6e8ea;--mut:#b39399;--red:#e23b50;--red-d:#b8283b;--glow:rgba(226,59,80,.30);--ok:#52d6a0;--warn:#f4b942;--term:#12060a;--mono:"Cascadia Mono","Cascadia Code",Consolas,monospace}
*{box-sizing:border-box}
html{color-scheme:dark}
body{margin:0;min-height:100vh;color:var(--tx);background:var(--bg);font:15px/1.5 "Segoe UI Variable Text","Segoe UI",system-ui,sans-serif}
button,input{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--red);outline-offset:2px}
.hidden{display:none!important}
.btn{display:inline-flex;align-items:center;gap:7px;min-height:38px;padding:0 14px;border-radius:8px;border:1px solid var(--line);background:var(--panel);cursor:pointer;font-weight:600;transition:background .15s,border-color .15s,box-shadow .15s}
.btn:hover{border-color:#6b2f3b;background:#34161f}
.btn:disabled{opacity:.5;cursor:default}
.btn.primary{background:var(--red);border-color:var(--red);color:#fff}
.btn.primary:hover{background:#f0495d;box-shadow:0 0 0 4px var(--glow)}
.btn.danger{border-color:#7d2a37;color:#ff8d9b}
.btn.small{min-height:32px;padding:0 11px;font-size:13px}
svg.i{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex:none}
/* login */
#login{min-height:100vh;display:grid;place-items:center;padding:20px}
.login-box{width:100%;max-width:380px}
.mark{width:52px;height:52px;border-radius:14px;background:var(--red);display:grid;place-items:center;box-shadow:0 0 0 8px var(--glow)}
.mark svg{width:28px;height:28px;stroke:#fff;fill:none;stroke-width:2.4;stroke-linecap:round;stroke-linejoin:round}
.login-box h1{font-size:30px;line-height:1.15;margin:28px 0 6px;letter-spacing:-.02em}
.login-box p{margin:0 0 22px;color:var(--mut)}
.field{display:flex;gap:8px}
.field input{flex:1;min-width:0;height:44px;padding:0 14px;border-radius:8px;border:1px solid var(--line);background:var(--rail)}
.field input:focus{outline:none;border-color:var(--red);box-shadow:0 0 0 4px var(--glow)}
.field .btn{height:44px}
#err{min-height:22px;margin:10px 2px 0;color:#ff8d9b;font-size:14px}
/* app */
header{display:flex;align-items:center;gap:12px;padding:14px 22px;border-bottom:1px solid var(--line);background:var(--rail)}
header .mark{width:34px;height:34px;border-radius:9px;box-shadow:none}
header .mark svg{width:19px;height:19px}
header h1{font-size:17px;margin:0;letter-spacing:-.01em}
.live{display:flex;align-items:center;gap:7px;margin-left:6px;color:var(--mut);font-size:13px}
.live::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 3px rgba(82,214,160,.18)}
.hbtns{margin-left:auto;display:flex;gap:8px}
main{display:grid;grid-template-columns:minmax(300px,390px) 1fr;min-height:calc(100vh - 63px)}
aside{background:var(--rail);border-right:1px solid var(--line);padding:6px 0 24px}
section.side{padding:18px 22px;border-bottom:1px solid var(--line)}
section.side:last-child{border-bottom:0}
.sh{display:flex;align-items:baseline;justify-content:space-between;margin:0 0 10px}
.sh h2{margin:0;font-size:15px;font-weight:650}
.sh span{color:var(--mut);font-size:13px}
.item{display:flex;align-items:center;gap:11px;padding:9px 0}
.item+.item{border-top:1px solid rgba(71,32,41,.55)}
.ext{flex:none;width:40px;height:26px;border-radius:6px;display:grid;place-items:center;font:600 11px var(--mono);background:#3a1822;color:#ffb3bd}
.ext.py{background:#3b2f12;color:#f4cf6a}.ext.ps1{background:#14263f;color:#8ec1ff}.ext.js{background:#3a3511;color:#efe36a}.ext.bat,.ext.cmd{background:#2b2b2b;color:#d0d0d0}.ext.vbs{background:#2c1a3f;color:#cfa8ff}
.name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.item.sel .name{color:#fff;font-weight:600}
.item.sel{box-shadow:inset 3px 0 0 var(--red);padding-left:10px;margin-left:-10px}
.chip{font-size:12px;font-weight:600;padding:2px 9px;border-radius:999px}
.chip.run{background:rgba(244,185,66,.14);color:var(--warn);animation:pulse 1.6s ease-in-out infinite}
.chip.ok{background:rgba(82,214,160,.14);color:var(--ok)}
.chip.stp{background:rgba(179,147,153,.16);color:var(--mut)}
.chip.bad{background:rgba(255,107,125,.16);color:#ff8d9b}
@keyframes pulse{50%{opacity:.55}}
.sub{display:block;color:var(--mut);font-size:12px}
.empty{color:var(--mut);font-size:14px;padding:6px 0}
.drop{display:flex;align-items:center;justify-content:center;gap:9px;padding:18px;border:1.5px dashed #6b2f3b;border-radius:10px;color:var(--mut);cursor:pointer;text-align:center;transition:.15s}
.drop:hover,.drop.over{border-color:var(--red);color:var(--tx);background:rgba(226,59,80,.08)}
/* console */
.stage{padding:22px;display:flex;flex-direction:column;min-width:0}
.console{display:flex;flex-direction:column;flex:1;min-height:420px;border:1px solid #6b2f3b;border-radius:12px;background:var(--term);overflow:hidden;box-shadow:0 0 0 1px rgba(226,59,80,.12),0 20px 60px -20px rgba(226,59,80,.45)}
.bar{display:flex;align-items:center;gap:10px;padding:8px 10px 8px 14px;background:var(--panel);border-bottom:1px solid var(--line)}
.tabs{display:flex;gap:4px}
.tab{height:32px;padding:0 13px;border-radius:7px;border:0;background:none;color:var(--mut);font-weight:600;cursor:pointer;display:flex;align-items:center;gap:7px}
.tab[aria-selected=true]{background:var(--term);color:var(--tx)}
.title{margin-left:auto;color:var(--mut);font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#out{flex:1;margin:0;padding:16px 18px;overflow:auto;font:13.5px/1.55 var(--mono);white-space:pre-wrap;word-break:break-word;color:#f1d9dd;max-height:calc(100vh - 190px)}
#out:empty::before{content:"Run a script or pick a job and its output shows up here.";color:var(--mut);font-family:"Segoe UI",system-ui,sans-serif}
.inbar{display:flex;gap:8px;padding:10px;border-top:1px solid var(--line);background:var(--panel)}
.inbar input{flex:1;min-width:0;height:36px;padding:0 12px;border-radius:8px;border:1px solid var(--line);background:var(--term);font:13.5px var(--mono)}
.inbar input:focus{outline:none;border-color:var(--red);box-shadow:0 0 0 3px var(--glow)}
.inbar input:disabled{opacity:.55}
.screen{flex:1;display:flex;flex-direction:column;padding:14px;gap:12px;overflow:auto}
.screen .row{display:flex;align-items:center;gap:12px;color:var(--mut);font-size:13px}
#shot{width:100%;border-radius:8px;border:1px solid var(--line)}
.toasts{position:fixed;right:18px;bottom:18px;display:flex;flex-direction:column;gap:8px;z-index:9}
.toast{padding:11px 16px;border-radius:9px;background:var(--panel);border:1px solid #6b2f3b;box-shadow:0 10px 30px rgba(0,0,0,.5);max-width:320px}
.toast.bad{border-color:var(--red);color:#ffb3bd}
@media(max-width:860px){main{grid-template-columns:1fr}aside{border-right:0}.stage{padding:14px}.console{min-height:380px}#out{max-height:60vh}}
body.bg{background:linear-gradient(rgba(26,9,13,.62),rgba(26,9,13,.82)),var(--wall) center/cover fixed no-repeat}
body.bg header,body.bg aside{background:rgba(33,13,18,.72);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px)}
body.bg .console{background:rgba(18,6,10,.84)}
body.bg .bar,body.bg .inbar{background:rgba(42,17,24,.82)}
body.bg .login-box{background:rgba(33,13,18,.78);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);padding:30px;border:1px solid var(--line);border-radius:14px}
@media(max-width:600px){.lbl{display:none}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style></head><body>
<svg width="0" height="0" style="position:absolute"><defs>
<symbol id="play" viewBox="0 0 24 24"><path d="M7 5l12 7-12 7z"/></symbol>
<symbol id="stop" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/></symbol>
<symbol id="up" viewBox="0 0 24 24"><path d="M12 16V4M7 9l5-5 5 5M5 20h14"/></symbol>
<symbol id="mon" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></symbol>
<symbol id="term" viewBox="0 0 24 24"><path d="M5 8l4 4-4 4M12 17h7"/></symbol>
<symbol id="pic" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="M21 16l-5-5-8 8"/></symbol>
<symbol id="exit" viewBox="0 0 24 24"><path d="M9 4H5v16h4M16 8l4 4-4 4M20 12H9"/></symbol>
</defs></svg>

<div id="login"><div class="login-box">
 <div class="mark"><svg viewBox="0 0 24 24"><path d="M5 8l4 4-4 4M12 17h7"/></svg></div>
 <h1>Script Runner</h1>
 <p>Enter the token from token.txt on the target PC.</p>
 <div class="field"><input id="tok" type="password" placeholder="Token" autocomplete="current-password" autofocus><button class="btn primary" id="go">Connect</button></div>
 <div id="err" role="alert"></div>
</div></div>

<div id="app" class="hidden">
<header>
 <div class="mark"><svg viewBox="0 0 24 24"><path d="M5 8l4 4-4 4M12 17h7"/></svg></div>
 <h1>Script Runner</h1><span class="live">Connected</span>
 <div class="hbtns">
  <button class="btn small" id="wall" aria-label="Change background"><svg class="i"><use href="#pic"/></svg><span class="lbl">Change background</span></button>
  <button class="btn small hidden" id="wallreset">Reset</button>
  <button class="btn small" id="logout" aria-label="Disconnect"><svg class="i"><use href="#exit"/></svg><span class="lbl">Disconnect</span></button>
  <input type="file" id="wallfile" accept="image/*" hidden>
 </div>
</header>
<main>
<aside>
 <section class="side"><div class="sh"><h2>Scripts</h2><span id="scount"></span></div><div id="scripts"></div></section>
 <section class="side"><div class="sh"><h2>Add scripts</h2></div>
  <label class="drop" id="drop"><svg class="i"><use href="#up"/></svg><span>Drop files here or click to choose</span><input type="file" id="file" multiple hidden></label></section>
 <section class="side"><div class="sh"><h2>Runs</h2><span id="jcount"></span></div><div id="jobs"></div></section>
</aside>
<div class="stage"><div class="console">
 <div class="bar" role="tablist">
  <div class="tabs">
   <button class="tab" role="tab" data-tab="out" aria-selected="true"><svg class="i"><use href="#term"/></svg>Output</button>
   <button class="tab" role="tab" data-tab="screen" aria-selected="false"><svg class="i"><use href="#mon"/></svg>Screen</button>
  </div><span class="title" id="cur"></span>
 </div>
 <pre id="out" tabindex="0"></pre>
 <div class="inbar" id="inbar"><input id="stdin" placeholder="No script is waiting for input" autocomplete="off" disabled><button class="btn primary small" id="send" disabled>Send</button></div>
 <div class="screen hidden" id="screen">
  <div class="row"><button class="btn primary small" id="view"><svg class="i"><use href="#mon"/></svg>View screen</button><span id="shotmsg">Takes a snapshot of the target display.</span></div>
  <img id="shot" class="hidden" alt="Screenshot of the target machine">
 </div>
</div></div>
</main></div>
<div class="toasts" id="toasts" aria-live="polite"></div>

<script>
const $ = s => document.querySelector(s);
let T = sessionStorage.getItem("tok") || "", current = null, timer = null, last = {};
const esc = s => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ico = n => `<svg class="i"><use href="#${n}"/></svg>`;
function toast(msg, bad){ const t = document.createElement("div"); t.className = "toast" + (bad ? " bad" : ""); t.textContent = msg; $("#toasts").append(t); setTimeout(() => t.remove(), 3500); }
async function api(path, opts = {}){
  opts.headers = Object.assign({"X-Token": T}, opts.headers || {});
  const r = await fetch(path, opts);
  if (r.status === 401){ const e = new Error("unauthorized"); e.auth = true; throw e; }
  return r;
}
const json = async (p, o) => (await api(p, o)).json();
function logout(){ sessionStorage.removeItem("tok"); location.reload(); }
async function login(){
  T = $("#tok").value.trim(); if (!T) return;
  $("#err").textContent = "";
  try { await json("/api/scripts"); sessionStorage.setItem("tok", T); enter(); }
  catch(e){ $("#err").textContent = e.auth ? "That token doesn't match. Check token.txt on the target PC." : "Can't reach the server. Is the program running?"; }
}
function enter(){ $("#login").classList.add("hidden"); $("#app").classList.remove("hidden"); refresh(); timer = setInterval(refresh, 1500); }
function setHTML(id, html){ if (last[id] !== html){ last[id] = html; $(id).innerHTML = html; } }
async function refresh(){
  try {
    const scripts = await json("/api/scripts");
    $("#scount").textContent = scripts.length ? scripts.length + " available" : "";
    setHTML("#scripts", scripts.map(s => `<div class="item"><span class="ext ${esc(s.split(".").pop().toLowerCase())}">${esc(s.split(".").pop().toLowerCase())}</span><span class="name" title="${esc(s)}">${esc(s)}</span><button class="btn primary small" data-run="${esc(s)}">${ico("play")}Run</button></div>`).join("") || `<div class="empty">No scripts yet. Add one below.</div>`);
    const jobs = await json("/api/jobs");
    $("#jcount").textContent = jobs.length ? jobs.length + " this session" : "";
    setHTML("#jobs", jobs.map(j => {
      const chip = j.running ? `<span class="chip run">Running</span>` : j.stopped ? `<span class="chip stp">Stopped</span>` : j.exit_code === 0 ? `<span class="chip ok">Finished</span>` : `<span class="chip bad">Failed (${j.exit_code})</span>`;
      return `<div class="item${j.id === current ? " sel" : ""}"><button class="btn small" data-view="${j.id}" style="flex:1;justify-content:flex-start;min-width:0"><span class="name">${esc(j.name)}</span></button><span class="sub">${j.started}</span>${chip}${j.running ? `<button class="btn danger small" data-stop="${j.id}" aria-label="Stop ${esc(j.name)}">${ico("stop")}</button>` : ""}</div>`;
    }).join("") || `<div class="empty">Nothing has run yet.</div>`);
    if (current){
      const d = await json("/api/jobs/" + current);
      if (d.error){ current = null; setInput(false); $("#out").textContent = ""; $("#cur").textContent = ""; return; }
      const o = $("#out"), stick = o.scrollTop + o.clientHeight >= o.scrollHeight - 24;
      if (o.textContent !== d.output){ o.textContent = d.output; if (stick) o.scrollTop = o.scrollHeight; }
      setInput(d.info.running);
      $("#cur").textContent = d.info.name + (d.info.running ? " is running" : d.info.stopped ? " was stopped" : " has finished");
    }
  } catch(e){ if (e.auth) logout(); }
}
function setInput(on){
  $("#stdin").disabled = !on; $("#send").disabled = !on;
  $("#stdin").placeholder = on ? "Type input for the script and press Enter" : "No script is waiting for input";
}
async function sendInput(){
  const i = $("#stdin"), text = i.value; if (!current) return;
  i.value = "";
  try { const r = await json("/api/jobs/" + current + "/input", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({text})}); r.error ? toast(r.error, true) : refresh(); }
  catch(e){ if (e.auth) logout(); }
}
function showTab(t){
  document.querySelectorAll(".tab").forEach(b => b.setAttribute("aria-selected", b.dataset.tab === t));
  $("#out").classList.toggle("hidden", t !== "out"); $("#inbar").classList.toggle("hidden", t !== "out"); $("#screen").classList.toggle("hidden", t !== "screen");
}
async function viewScreen(){
  const b = $("#view"), m = $("#shotmsg"), img = $("#shot");
  b.disabled = true; m.textContent = "Capturing...";
  try {
    const r = await api("/api/screenshot");
    if (!r.ok){ m.textContent = "Capture failed. The PC may be locked or asleep."; return; }
    if (img.src.startsWith("blob:")) URL.revokeObjectURL(img.src);
    img.src = URL.createObjectURL(await r.blob()); img.classList.remove("hidden");
    m.textContent = "Taken at " + new Date().toLocaleTimeString();
  } catch(e){ if (e.auth) logout(); else m.textContent = "Can't reach the server."; }
  finally { b.disabled = false; }
}
const WALL = "wall";
function applyWall(url){
  if (url){ document.body.style.setProperty("--wall", `url("${url}")`); document.body.classList.add("bg"); }
  else { document.body.style.removeProperty("--wall"); document.body.classList.remove("bg"); }
  $("#wallreset").classList.toggle("hidden", !url);
}
function pickWall(file){
  const img = new Image(), u = URL.createObjectURL(file);
  img.onload = () => {
    const k = Math.min(1, 1920 / Math.max(img.width, img.height));
    const c = document.createElement("canvas"); c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
    c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
    URL.revokeObjectURL(u);
    const data = c.toDataURL("image/jpeg", 0.82);
    applyWall(data);
    try { localStorage.setItem(WALL, data); toast("Background updated"); }
    catch(e){ toast("Background applied, but this browser can't keep it after you close the page.", true); }
  };
  img.onerror = () => { URL.revokeObjectURL(u); toast("That file isn't an image this browser can open.", true); };
  img.src = u;
}
async function uploadFiles(files){
  for (const f of files){
    const fd = new FormData(); fd.append("file", f);
    try { const r = await json("/api/upload", {method: "POST", body: fd}); r.error ? toast(f.name + ": " + r.error, true) : toast("Added " + r.saved); }
    catch(e){ toast("Couldn't upload " + f.name, true); }
  }
  refresh();
}
document.addEventListener("click", async e => {
  const el = e.target.closest("button"); if (!el) return; const d = el.dataset;
  if (d.run){ const j = await json("/api/run", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({name: d.run})}); if (j.error) return toast(j.error, true); current = j.id; showTab("out"); await refresh(); $("#stdin").focus(); }
  if (d.view){ current = d.view; showTab("out"); refresh(); }
  if (d.stop){ await json("/api/jobs/" + d.stop + "/stop", {method: "POST"}); toast("Stopped"); refresh(); }
  if (d.tab) showTab(d.tab);
});
$("#go").onclick = login; $("#tok").onkeydown = e => { if (e.key === "Enter") login(); };
$("#send").onclick = sendInput; $("#stdin").onkeydown = e => { if (e.key === "Enter") sendInput(); };
$("#wall").onclick = () => $("#wallfile").click();
$("#wallfile").onchange = e => { const f = e.target.files[0]; if (f) pickWall(f); e.target.value = ""; };
$("#wallreset").onclick = () => { applyWall(null); try { localStorage.removeItem(WALL); } catch(e){} toast("Background reset"); };
try { applyWall(localStorage.getItem(WALL)); } catch(e){}
$("#logout").onclick = logout; $("#view").onclick = viewScreen;
$("#file").onchange = e => { uploadFiles(e.target.files); e.target.value = ""; };
const drop = $("#drop");
["dragenter","dragover"].forEach(v => drop.addEventListener(v, e => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave","drop"].forEach(v => drop.addEventListener(v, e => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", e => uploadFiles(e.dataTransfer.files));
if (T){ json("/api/scripts").then(enter).catch(() => {}); }
</script></body></html>
"""


if __name__ == "__main__":
    from waitress import serve
    print(f"Token is in {TOKEN_FILE}")
    print(f"Serving on port {PORT}")
    serve(app, host="0.0.0.0", port=PORT)
