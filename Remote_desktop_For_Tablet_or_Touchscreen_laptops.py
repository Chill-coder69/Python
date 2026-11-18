"""
Remote Touchpad + Keyboard
--------------------------
Run this on the PC you want to CONTROL, then open the printed URL on your phone
(same Wi-Fi) and enter the PIN shown in the terminal.

    pip install flask flask-sock pyautogui
    python app.py

Optional environment variables:  REMOTE_PIN=123456   PORT=5000
"""
import hmac
import json
import os
import secrets
import socket
import sys
import threading
import time
from urllib.parse import urlparse

import pyautogui
from flask import Flask, Response, redirect, request, session, url_for
from flask_sock import Sock

# ----------------------------------------------------------------- config ----
PORT = int(os.environ.get("PORT", 5000))
PIN = os.environ.get("REMOTE_PIN") or f"{secrets.randbelow(10**6):06d}"
SCROLL_UNIT = 120 if sys.platform == "win32" else 1  # pyautogui: 120 = 1 notch on Windows

pyautogui.PAUSE = 0          # default 0.1s pause after every call makes the mouse laggy
pyautogui.FAILSAFE = False   # otherwise a remote move into a screen corner raises an exception
pyautogui.MINIMUM_DURATION = 0

ALLOWED_KEYS = set(pyautogui.KEYBOARD_KEYS)
ALLOWED_BUTTONS = {"left", "right", "middle"}
MEDIA_KEYS = ["prevtrack", "playpause", "nexttrack", "stop", "volumedown", "volumemute", "volumeup"]

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_HTTPONLY=True)
sock = Sock(app)
io_lock = threading.Lock()

# ------------------------------------------------------------------- auth ----
_fails = {}  # ip -> (count, locked_until)


@app.before_request
def guard():
    if request.endpoint in ("login", "static"):
        return None
    if not session.get("ok"):
        return redirect(url_for("login"))
    return None


@app.route("/login", methods=["GET", "POST"])
def login():
    err = ""
    ip = request.remote_addr
    count, until = _fails.get(ip, (0, 0))
    if request.method == "POST":
        if time.time() < until:
            err = "Too many attempts. Wait a minute."
        elif hmac.compare_digest(request.form.get("pin", ""), PIN):
            _fails.pop(ip, None)
            session["ok"] = True
            return redirect("/")
        else:
            count += 1
            _fails[ip] = (count, time.time() + 60 if count >= 5 else 0)
            if count >= 5:
                _fails[ip] = (0, time.time() + 60)
            err = "Wrong PIN."
    body = f"""
    <main class="center">
      <h1>Enter PIN</h1>
      <p class="muted">Shown in the terminal where the server is running.</p>
      <form method="post">
        <input name="pin" inputmode="numeric" autocomplete="off" autofocus placeholder="••••••">
        <button class="big" type="submit">Connect</button>
      </form>
      <p class="err">{err}</p>
    </main>"""
    return page("Login", body, body_class="")


# ------------------------------------------------------------ input engine ----
def handle(msg, held_keys, held_btns):
    t = msg.get("t")
    with io_lock:
        if t == "move":
            dx = max(-500, min(500, int(msg.get("dx", 0))))
            dy = max(-500, min(500, int(msg.get("dy", 0))))
            pyautogui.moveRel(dx, dy)
        elif t == "click":
            b = msg.get("b")
            if b in ALLOWED_BUTTONS:
                pyautogui.click(button=b)
        elif t == "mdown":
            b = msg.get("b")
            if b in ALLOWED_BUTTONS:
                pyautogui.mouseDown(button=b)
                held_btns.add(b)
        elif t == "mup":
            b = msg.get("b")
            if b in ALLOWED_BUTTONS:
                pyautogui.mouseUp(button=b)
                held_btns.discard(b)
        elif t == "scroll":
            v = max(-50, min(50, int(msg.get("v", 0))))
            h = max(-50, min(50, int(msg.get("h", 0))))
            if v:
                pyautogui.scroll(v * SCROLL_UNIT)
            if h:
                try:
                    pyautogui.hscroll(h * SCROLL_UNIT)
                except Exception:
                    pass  # horizontal scroll isn't supported on every platform
        elif t == "kdown":
            k = msg.get("k")
            if k in ALLOWED_KEYS:
                pyautogui.keyDown(k)
                held_keys.add(k)
        elif t == "kup":
            k = msg.get("k")
            if k in ALLOWED_KEYS:
                pyautogui.keyUp(k)
                held_keys.discard(k)
        elif t == "tap":
            k = msg.get("k")
            if k in ALLOWED_KEYS:
                pyautogui.press(k)
        elif t == "reset":
            release_all(held_keys, held_btns)


def release_all(held_keys, held_btns):
    """Never leave a key or mouse button stuck down on the target machine."""
    for k in list(held_keys):
        try:
            pyautogui.keyUp(k)
        except Exception:
            pass
    for b in list(held_btns):
        try:
            pyautogui.mouseUp(button=b)
        except Exception:
            pass
    held_keys.clear()
    held_btns.clear()


@sock.route("/ws")
def ws(ws):
    # Reject cross-site WebSocket hijacking attempts.
    origin = request.headers.get("Origin")
    if origin and urlparse(origin).netloc != request.host:
        ws.close()
        return
    held_keys, held_btns = set(), set()
    try:
        while True:
            data = ws.receive()
            if data is None:
                break
            try:
                handle(json.loads(data), held_keys, held_btns)
            except Exception as exc:  # bad message or pyautogui error: log and keep going
                print("input error:", exc)
    finally:
        with io_lock:
            release_all(held_keys, held_btns)


# ------------------------------------------------------------------ pages ----
CSS = r"""
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;height:100%;background:#0f1115;color:#e8eaed;font-family:system-ui,-apple-system,Segoe UI,sans-serif}
a{color:inherit;text-decoration:none}
.center{min-height:100dvh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:16px;padding:20px}
.muted{color:#8b93a1;margin:0}.err{color:#ff6b6b;min-height:1.2em}
.cards{display:flex;gap:20px;flex-wrap:wrap;justify-content:center}
.card{width:min(260px,80vw);padding:36px 20px;border:2px solid #fff;border-radius:20px;text-align:center;font-size:1.4rem;background:#171a21}
.card small{display:block;margin-top:8px;font-size:.85rem;color:#8b93a1}
.card:active{background:#252a35}
input{font-size:1.6rem;text-align:center;letter-spacing:.3em;padding:12px;border-radius:12px;border:2px solid #444;background:#171a21;color:#fff;width:220px}
.big{display:block;margin:14px auto 0;font-size:1.1rem;padding:12px 28px;border-radius:12px;border:0;background:#4c8dff;color:#fff}
/* control pages */
body.ctl{display:flex;flex-direction:column;height:100dvh;overflow:hidden;touch-action:none;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none}
.top{display:flex;align-items:center;gap:12px;padding:8px 12px;font-size:.95rem}
.top .sp{flex:1}
.dot{width:12px;height:12px;border-radius:50%;background:#ff5252}.dot.ok{background:#3ddc84}
.btn{padding:8px 14px;border:1px solid #444;border-radius:10px;background:#171a21;color:#e8eaed;font-size:.9rem}
#pad{flex:1;margin:4px 10px;border:3px solid #fff;border-radius:18px;display:flex;align-items:center;justify-content:center;color:#3a404c}
.mb{display:flex;gap:8px;padding:6px 10px}
.mb .b{flex:1;height:60px;border:2px solid #fff;border-radius:14px;display:flex;align-items:center;justify-content:center;background:#171a21}
.mb .b.mid{flex:.4}.mb .b.hold{flex:.6}.mb .b.on{background:#4c8dff}.mb .b.hold.on{background:#fff;color:#000}
.opts{display:flex;gap:16px;align-items:center;padding:6px 14px 12px;font-size:.9rem;color:#8b93a1}
.opts input[type=range]{width:140px;letter-spacing:normal;padding:0;border:0;background:none}
#kbwrap{flex:1;display:flex;align-items:center;justify-content:center}
#kb{--u:calc(min(100vw,1300px)/18.4);--h:calc(var(--u)*.92)}
.row{display:flex;height:var(--h)}.row.gapb{margin-bottom:calc(var(--u)*.35)}
.key,.gap{flex:none;width:calc(var(--u)*var(--w))}
.key{padding:2px}
.cap{height:100%;border:1.5px solid #fff;border-radius:7px;background:#171a21;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1.05;font-size:calc(var(--u)*.3);overflow:hidden}
.cap .s{font-size:.7em;color:#8b93a1}
.cap.one .m{font-size:1em}
.key.on .cap{background:#4c8dff;border-color:#4c8dff}
.key.charging .cap{background:#fff;color:#000;transition:background 3s linear,color 3s linear}
.key.charging .cap .s,.key.latched .cap .s{color:#555}
.key.latched .cap{background:#fff;color:#000;border-color:#fff}
.key.down .cap{background:#2d3442}
.mgrid{flex:1;display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:12px;align-content:center}
.mk{min-height:96px;border:2px solid #fff;border-radius:16px;background:#171a21;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;font-size:2rem}
.mk small{font-size:.8rem;color:#8b93a1}
.mk.wide{grid-column:1/-1;min-height:64px;flex-direction:row;gap:12px;font-size:1.5rem}
.mk.on{background:#fff;color:#000}.mk.on small{color:#555}
.hint{display:none;text-align:center;color:#8b93a1;font-size:.85rem;padding:4px}
@media (orientation:portrait){.hint{display:block}}
"""

COMMON_JS = r"""
let ws, ready = false;
const dot = document.getElementById('dot');
function connect() {
  ws = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');
  ws.onopen = () => { ready = true; dot.className = 'dot ok'; };
  ws.onclose = () => { ready = false; dot.className = 'dot'; if (window.onDisconnect) onDisconnect(); setTimeout(connect, 1000); };
}
function send(o) { if (ready) ws.send(JSON.stringify(o)); }
connect();
document.addEventListener('contextmenu', e => e.preventDefault());
"""

MOUSE_JS = r"""
const pad = document.getElementById('pad');
let sens = parseFloat(localStorage.sens || '1.6'), natural = localStorage.nat !== '0';
const sl = document.getElementById('sens'), nat = document.getElementById('nat');
sl.value = sens; nat.checked = natural;
sl.oninput = () => { sens = parseFloat(sl.value); localStorage.sens = sens; };
nat.onchange = () => { natural = nat.checked; localStorage.nat = natural ? '1' : '0'; };

let ax = 0, ay = 0, pend = false, sx = 0, sy = 0;
let last = {x: 0, y: 0}, t0 = 0, moved = 0, maxT = 0, lastTap = 0, dragging = false, holdOn = false;
const STEP = 30; // px of two-finger travel per scroll notch

const mid = ts => { let x = 0, y = 0; for (const t of ts) { x += t.clientX; y += t.clientY; } return {x: x / ts.length, y: y / ts.length}; };

function flush() {
  if (pend) return; pend = true;
  requestAnimationFrame(() => {
    pend = false;
    const ix = Math.trunc(ax), iy = Math.trunc(ay);
    if (ix || iy) { ax -= ix; ay -= iy; send({t: 'move', dx: ix, dy: iy}); }
  });
}

pad.addEventListener('touchstart', e => {
  e.preventDefault();
  const n = e.touches.length;
  if (n === 1) {
    t0 = Date.now(); moved = 0; maxT = 1;
    if (!holdOn && Date.now() - lastTap < 250) { dragging = true; send({t: 'mdown', b: 'left'}); }
  } else maxT = Math.max(maxT, n);
  last = mid(e.touches);
}, {passive: false});

pad.addEventListener('touchmove', e => {
  e.preventDefault();
  const p = mid(e.touches), dx = p.x - last.x, dy = p.y - last.y;
  last = p; moved += Math.abs(dx) + Math.abs(dy);
  if (e.touches.length === 1) {
    const f = sens * (1 + Math.min(Math.hypot(dx, dy), 30) / 30); // light acceleration
    ax += dx * f; ay += dy * f; flush();
  } else if (e.touches.length === 2 && !dragging) {
    sx += dx; sy += dy;
    const nv = Math.trunc(sy / STEP), nh = Math.trunc(sx / STEP);
    if (nv || nh) {
      sy -= nv * STEP; sx -= nh * STEP;
      send({t: 'scroll', v: natural ? nv : -nv, h: natural ? -nh : nh});
    }
  }
}, {passive: false});

function endTouch(e, cancelled) {
  e.preventDefault();
  if (e.touches.length === 0) {
    if (dragging) { send({t: 'mup', b: 'left'}); dragging = false; lastTap = 0; }
    else if (!cancelled && Date.now() - t0 < 220 && moved < 10) {
      if (maxT === 1) { if (!holdOn) { send({t: 'click', b: 'left'}); lastTap = Date.now(); } }  // a tap would end the hold
      else if (maxT === 2) send({t: 'click', b: 'right'});
    }
    maxT = 0; sx = sy = 0;
  } else last = mid(e.touches);
}
pad.addEventListener('touchend', e => endTouch(e, false), {passive: false});
pad.addEventListener('touchcancel', e => endTouch(e, true), {passive: false});

// Hold button: toggles the left mouse button held down (drag lock). White = held.
const holdBtn = document.getElementById('hold');
function setHold(on) {
  if (on === holdOn || (on && dragging)) return;
  holdOn = on; holdBtn.classList.toggle('on', on);
  send({t: on ? 'mdown' : 'mup', b: 'left'});
}
holdBtn.addEventListener('pointerdown', e => { e.preventDefault(); setHold(!holdOn); });
window.onDisconnect = () => { holdOn = false; dragging = false; holdBtn.classList.remove('on'); };  // server releases the button when the socket drops

document.querySelectorAll('.mb .b[data-b]').forEach(b => {
  const btn = b.dataset.b;
  b.addEventListener('pointerdown', e => { e.preventDefault(); if (btn === 'left' && holdOn) { setHold(false); return; } b.setPointerCapture(e.pointerId); b.classList.add('on'); send({t: 'mdown', b: btn}); });
  const up = () => { if (b.classList.contains('on')) { b.classList.remove('on'); send({t: 'mup', b: btn}); } };
  b.addEventListener('pointerup', up); b.addEventListener('pointercancel', up);
});
"""

KEYBOARD_JS = r"""
const K = (l, k, w = 1, s) => ({l, k, w, s});
const G = w => ({g: w});
const pairs = a => a.map(([c, s, w]) => K(c, c, w || 1, s));
const letters = s => s.split('').map(c => K(c.toUpperCase(), c));

const LAYOUT = [
  [K('Esc','esc'), G(1), ...[1,2,3,4].map(n => K('F'+n,'f'+n)), G(.5), ...[5,6,7,8].map(n => K('F'+n,'f'+n)), G(.5),
   ...[9,10,11,12].map(n => K('F'+n,'f'+n)), G(.25), K('PrtSc','printscreen'), K('ScrLk','scrolllock'), K('Pause','pause')],
  [...pairs([['`','~'],['1','!'],['2','@'],['3','#'],['4','$'],['5','%'],['6','^'],['7','&'],['8','*'],['9','('],['0',')'],['-','_'],['=','+']]),
   K('Backspace','backspace',2), G(.25), K('Ins','insert'), K('Home','home'), K('PgUp','pageup')],
  [K('Tab','tab',1.5), ...letters('qwertyuiop'), ...pairs([['[','{'],[']','}']]), K('\\','\\',1.5,'|'), G(.25),
   K('Del','delete'), K('End','end'), K('PgDn','pagedown')],
  [K('Caps','capslock',1.75), ...letters('asdfghjkl'), ...pairs([[';',':'],["'",'"']]), K('Enter','enter',2.25), G(3.25)],
  [K('Shift','shiftleft',2.25), ...letters('zxcvbnm'), ...pairs([[',','<'],['.','>'],['/','?']]), K('Shift','shiftright',2.75),
   G(1.25), K('\u2191','up'), G(1)],
  [K('Ctrl','ctrlleft',1.25), K('Win','winleft',1.25), K('Alt','altleft',1.25), K('Space','space',6.25), K('Alt','altright',1.25),
   K('Win','winright',1.25), K('Menu','apps',1.25), K('Ctrl','ctrlright',1.25), G(.25), K('\u2190','left'), K('\u2193','down'), K('\u2192','right')],
];

const MODS = new Set(['shiftleft','shiftright','ctrlleft','ctrlright','altleft','altright','winleft','winright']);
const NOREPEAT = new Set([...MODS, 'capslock','esc','printscreen','scrolllock','pause','apps']);
const HOLD_MS = 3000;  // hold a modifier this long to arm it for the next key
const st = {};

function press(k)   { const s = st[k]; send({t:'kdown', k}); s.down = true;  s.el.classList.add('on'); }
function release(k) { const s = st[k]; send({t:'kup', k});   s.down = false; s.el.classList.remove('on'); }
function unlatch(k) { const s = st[k]; s.latched = false; s.el.classList.remove('latched'); }
function cancelCharge(s) { clearTimeout(s.lt); s.el.classList.remove('charging'); }

function bind(el, k) {
  const s = st[k] = {el, down: false, phys: false, latched: false, fired: false, used: false, cancel: false, lt: null, rep: null, rt: null};

  el.addEventListener('pointerdown', e => {
    e.preventDefault(); el.setPointerCapture(e.pointerId);
    if (MODS.has(k)) {
      if (s.latched) { unlatch(k); s.cancel = true; return; }   // tap an armed modifier to disarm it
      s.cancel = false; s.phys = true; s.fired = false; s.used = false;
      el.classList.add('charging');                              // fills white over HOLD_MS
      s.lt = setTimeout(() => {
        el.classList.remove('charging');
        s.latched = true; s.fired = true;
        el.classList.add('latched');
        if (navigator.vibrate) navigator.vibrate(40);
      }, HOLD_MS);
      return;
    }
    // Normal key: send every armed modifier (3 s hold) or physically held modifier first.
    for (const m of MODS) {
      const ms = st[m];
      if (ms.latched || ms.phys) {
        if (ms.phys && !ms.fired) { cancelCharge(ms); ms.used = true; }   // multitouch hold: no latch afterwards
        if (!ms.down) press(m);
      }
    }
    press(k); el.classList.add('down');
    if (!NOREPEAT.has(k)) s.rt = setTimeout(() => { s.rep = setInterval(() => send({t:'kdown', k}), 45); }, 400);
  });

  const up = () => {
    if (MODS.has(k)) {
      if (s.cancel) { s.cancel = false; return; }
      if (!s.phys) return;
      s.phys = false;
      cancelCharge(s);
      if (s.fired) return;                                        // armed: wait for the next key
      if (s.used) { if (s.down) release(k); return; }             // was held as part of a multitouch combo
      send({t:'kdown', k}); send({t:'kup', k});                   // short press = normal single key press
    } else {
      if (!s.down) return;
      clearTimeout(s.rt); clearInterval(s.rep);
      release(k); el.classList.remove('down');
      for (const m of MODS) {                                     // armed modifiers are one-shot
        if (st[m].latched) { if (st[m].down) release(m); unlatch(m); }
      }
    }
  };
  el.addEventListener('pointerup', up); el.addEventListener('pointercancel', up);
}

const kb = document.getElementById('kb');
LAYOUT.forEach((row, i) => {
  const r = document.createElement('div'); r.className = 'row' + (i === 0 ? ' gapb' : '');
  row.forEach(d => {
    const e = document.createElement('div');
    if (d.g !== undefined) { e.className = 'gap'; e.style.setProperty('--w', d.g); }
    else {
      e.className = 'key'; e.style.setProperty('--w', d.w);
      const one = !d.s;
      e.innerHTML = '<div class="cap' + (one ? ' one' : '') + '">' + (one ? '' : '<span class="s"></span>') + '<span class="m"></span></div>';
      if (!one) e.querySelector('.s').textContent = d.s;
      e.querySelector('.m').textContent = d.l;
      bind(e, d.k);
    }
    r.appendChild(e);
  });
  kb.appendChild(r);
});

function resetAll() { for (const k in st) { const s = st[k]; clearTimeout(s.rt); clearTimeout(s.lt); clearInterval(s.rep);
  s.down = s.phys = s.latched = s.fired = s.used = s.cancel = false; s.el.classList.remove('on','down','latched','charging'); } }
function onDisconnect() { resetAll(); }   // the server releases everything when the socket drops
document.getElementById('rel').onclick = () => { send({t: 'reset'}); resetAll(); };
"""

HOME = r"""
<main class="center">
  <h1>Remote Control</h1>
  <div class="cards">
    <a class="card" href="/mouse">Mouse<small>touchpad &amp; clicks</small></a>
    <a class="card" href="/keyboard">Keyboard<small>full layout &amp; shortcuts</small></a>
    <a class="card" href="/media">Media<small>play, volume &amp; tracks</small></a>
  </div>
</main>
"""

MOUSE = r"""
<div class="top"><a class="btn" href="/">&larr; Home</a><span class="sp"></span><span class="muted">Mouse</span><span id="dot" class="dot"></span></div>
<div id="pad"><span>touchpad</span></div>
<div class="mb">
  <div class="b" data-b="left">Left</div><div class="b hold" id="hold">Hold</div><div class="b mid" data-b="middle">Mid</div><div class="b" data-b="right">Right</div>
</div>
<div class="opts">
  <label>Speed <input id="sens" type="range" min="0.5" max="4" step="0.1"></label>
  <label><input id="nat" type="checkbox"> Natural scroll</label>
</div>
"""

KEYBOARD = r"""
<div class="top"><a class="btn" href="/">&larr; Home</a><span class="sp"></span>
  <button class="btn" id="rel">Release all</button><span id="dot" class="dot"></span></div>
<div class="hint">Rotate your phone to landscape for a usable keyboard.</div>
<div id="kbwrap"><div id="kb"></div></div>
<div class="hint" style="display:block">Shortcuts: hold Ctrl / Shift / Alt / Win for 3 s until it turns white, then press the next key. Tap an armed key to cancel. A quick tap is a normal key press.</div>
"""


MEDIA = r"""
<div class="top"><a class="btn" href="/">&larr; Home</a><span class="sp"></span><span class="muted">Media</span><span id="dot" class="dot"></span></div>
<div class="mgrid">
  <div class="mk" data-k="prevtrack">&#9198;<small>Previous</small></div>
  <div class="mk" data-k="playpause">&#9199;<small>Play / Pause</small></div>
  <div class="mk" data-k="nexttrack">&#9197;<small>Next</small></div>
  <div class="mk" data-k="volumedown" data-rep="1">&#128265;<small>Volume &minus;</small></div>
  <div class="mk" data-k="volumemute">&#128263;<small>Mute</small></div>
  <div class="mk" data-k="volumeup" data-rep="1">&#128266;<small>Volume +</small></div>
  <div class="mk wide" data-k="stop">&#9209;<small>Stop</small></div>
</div>
"""

MEDIA_JS = r"""
document.querySelectorAll('.mk').forEach(b => {
  const k = b.dataset.k, rep = b.dataset.rep === '1';
  let rt = null, ri = null;
  const stop = () => { clearTimeout(rt); clearInterval(ri); b.classList.remove('on'); };
  b.addEventListener('pointerdown', e => {
    e.preventDefault(); b.setPointerCapture(e.pointerId); b.classList.add('on');
    send({t: 'tap', k});
    if (rep) rt = setTimeout(() => { ri = setInterval(() => send({t: 'tap', k}), 120); }, 400);  // hold volume to keep changing it
  });
  b.addEventListener('pointerup', stop); b.addEventListener('pointercancel', stop);
});
"""


def page(title, body, script="", body_class="ctl"):
    html = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">'
        f"<title>{title}</title><style>{CSS}</style></head>"
        f'<body class="{body_class}">{body}'
        + (f"<script>{COMMON_JS}{script}</script>" if script else "")
        + "</body></html>"
    )
    return Response(html, mimetype="text/html")


@app.route("/")
def home():
    return page("Remote Control", HOME, body_class="")


@app.route("/mouse")
def mouse():
    return page("Mouse", MOUSE, MOUSE_JS)


@app.route("/keyboard")
def keyboard():
    return page("Keyboard", KEYBOARD, KEYBOARD_JS)


@app.route("/media")
def media():
    return page("Media", MEDIA, MEDIA_JS)


# -------------------------------------------------------------------- main ----
def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    print("\n  Remote Touchpad + Keyboard")
    print(f"  Open on your phone:  http://{local_ip()}:{PORT}")
    print(f"  PIN:                 {PIN}")
    missing = [k for k in MEDIA_KEYS if k not in ALLOWED_KEYS]
    if missing:
        print(f"  WARNING: this pyautogui build has no media keys: {', '.join(missing)}")
    print("  (Plain HTTP: only use this on a network you trust.  Ctrl+C here to stop.)\n")
    app.run(host="0.0.0.0", port=PORT, threaded=True)
