from flask import Flask, render_template_string, request
from flask_socketio import SocketIO
import pyautogui

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

SENSITIVITY = 2

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remote</title>

    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>

    <style>

        *{
            box-sizing:border-box;
        }

        body{
            text-align:center;
            font-family:Arial,sans-serif;
            background:#111;
            color:white;
            margin:0;
            padding:15px;
        }

        #touchpad{
            width:95vw;
            height:50vh;
            min-height:300px;
            margin:20px auto;
            background:#333;
            border-radius:15px;
            border:3px solid white;
            touch-action:none;
        }

        button{
            height:60px;
            font-size:18px;
            background-color:#e74c3c;
            border-radius:15px;
            border:none;
            color:white;
            width:100%;
        }

        .write{
            max-width:600px;
        }

        #textinput,
        #textshortcut{
            width:95%;
            max-width:600px;
            height:50px;
            font-size:18px;
            border-radius:10px;
            border:none;
            padding-left:10px;
            margin-bottom:10px;
        }

        .button-container{
            width:95vw;
            margin:auto;
            display:grid;
            grid-template-columns:repeat(2,1fr);
            gap:10px;
        }

        form{
            margin-bottom:10px;
        }

    </style>
</head>

<body>

    <form action="/write" method="post">
        <input
            type="text"
            id="textinput"
            name="textinput"
            placeholder="Enter text here"
            required>
        <br>
        <button type="submit" class="write">Write</button>
    </form>

    <form action="/shortcut" method="post">
        <input
            type="text"
            id="textshortcut"
            name="textinput"
            placeholder="Enter shortcut here"
            required>
        <br>
        <button type="submit" class="write">Press Shortcut</button>
    </form>

    <div id="touchpad"></div>

    <div class="button-container">

        <button id="lmb">LMB</button>
        <button id="rmb">RMB</button>

        <button id="md">Drag Start</button>
        <button id="mu">Drag End</button>

        <button id="su">Scroll Up</button>
        <button id="sd">Scroll Down</button>

    </div>

<script>

const socket = io();

const touchpad = document.getElementById("touchpad");

let lastX = null;
let lastY = null;
let isTracking = false;
let lastSend = 0;

function startTracking(x,y){
    lastX = x;
    lastY = y;
    isTracking = true;
}

function moveTracking(x,y){

    if(!isTracking) return;

    const now = Date.now();

    if(now - lastSend < 8){
        return;
    }

    lastSend = now;

    let dx = x - lastX;
    let dy = y - lastY;

    lastX = x;
    lastY = y;

    socket.emit("move",{
        dx:dx,
        dy:dy
    });
}

function stopTracking(){
    isTracking = false;
}

/* Desktop */

touchpad.addEventListener("mousedown",(e)=>{
    startTracking(e.clientX,e.clientY);
});

touchpad.addEventListener("mousemove",(e)=>{
    moveTracking(e.clientX,e.clientY);
});

touchpad.addEventListener("mouseup",stopTracking);
touchpad.addEventListener("mouseleave",stopTracking);

/* Mobile */

touchpad.addEventListener("touchstart",(e)=>{
    const t = e.touches[0];
    startTracking(t.clientX,t.clientY);
});

touchpad.addEventListener("touchmove",(e)=>{
    e.preventDefault();

    const t = e.touches[0];

    moveTracking(
        t.clientX,
        t.clientY
    );
});

touchpad.addEventListener("touchend",stopTracking);

/* Buttons */

document.getElementById("lmb")
.addEventListener("click",()=>{
    socket.emit("left_click");
});

document.getElementById("rmb")
.addEventListener("click",()=>{
    socket.emit("right_click");
});

document.getElementById("md")
.addEventListener("click",()=>{
    socket.emit("mouse_down");
});

document.getElementById("mu")
.addEventListener("click",()=>{
    socket.emit("mouse_up");
});

document.getElementById("su")
.addEventListener("click",()=>{
    socket.emit("scroll_up");
});

document.getElementById("sd")
.addEventListener("click",()=>{
    socket.emit("scroll_down");
});

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/write", methods=["POST"])
def write_text():

    text = request.form["textinput"]

    pyautogui.write(
        text,
        interval=0.2
    )

    return ("",204)

@app.route("/shortcut", methods=["POST"])
def shortcut():

    text = request.form["textinput"]

    if "+" in text:

        parts = text.split("+")

        if len(parts) == 2:

            pyautogui.hotkey(
                parts[0],
                parts[1]
            )

        elif len(parts) == 3:

            pyautogui.hotkey(
                parts[0],
                parts[1],
                parts[2]
            )

    else:

        pyautogui.press(text)

    return ("",204)

@socketio.on("move")
def handle_move(data):

    dx = float(data["dx"])
    dy = float(data["dy"])

    pyautogui.moveRel(
        dx * SENSITIVITY,
        dy * SENSITIVITY
    )

@socketio.on("left_click")
def left_click():
    pyautogui.click()

@socketio.on("right_click")
def right_click():
    pyautogui.click(button="right")

@socketio.on("mouse_down")
def mouse_down():
    pyautogui.mouseDown()

@socketio.on("mouse_up")
def mouse_up():
    pyautogui.mouseUp()

@socketio.on("scroll_up")
def scroll_up():
    pyautogui.scroll(40)

@socketio.on("scroll_down")
def scroll_down():
    pyautogui.scroll(-40)

if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000
    )
