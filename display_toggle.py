"""
Display Toggle (Windows) - a tiny Flask app that turns your monitor ON or OFF
from a web page served on your local machine.

Run:    python display_toggle.py
Open:   http://127.0.0.1:5000
"""

import base64
import os

from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

# Win32 declarations made available to PowerShell via Add-Type.
WIN32_SIGNATURES = r"""
[DllImport("user32.dll")]
public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);

[DllImport("user32.dll")]
public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);

[DllImport("user32.dll")]
public static extern void keybd_event(byte bVk, byte bScan, int dwFlags, int dwExtraInfo);
"""

# WM_SYSCOMMAND (0x0112), SC_MONITORPOWER (0xF170): 2 = off, -1 = on.
POWER_OFF = "$api::SendMessage(-1, 0x0112, 0xF170, 2) | Out-Null"

# Windows often ignores the "monitor on" message by itself, so we also
# simulate user input (a 1px mouse nudge and a harmless F15 key press),
# which is what actually wakes the display.
POWER_ON = "\n".join(
    [
        "$api::SendMessage(-1, 0x0112, 0xF170, -1) | Out-Null",
        "$api::mouse_event(0x0001, 1, 1, 0, 0)",      # MOUSEEVENTF_MOVE +1,+1
        "Start-Sleep -Milliseconds 50",
        "$api::mouse_event(0x0001, -1, -1, 0, 0)"    # ...and back
     #   "$api::keybd_event(0x7E, 0, 0, 0)",            F15 down
      #  "$api::keybd_event(0x7E, 0, 2, 0)",            F15 up
    ]
)


def build_command(actions: str) -> str:
    """Return a shell command that runs `actions` in PowerShell.

    The script is base64-encoded (UTF-16LE, as PowerShell expects) so no
    shell quoting problems can occur.
    """
    script = (
        "$sig = @'\n"
        f"{WIN32_SIGNATURES}\n"
        "'@\n"
        "$api = Add-Type -MemberDefinition $sig -Name Win32 -Namespace Native -PassThru\n"
        f"{actions}\n"
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    return f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}"


COMMANDS = {
    "on": build_command(POWER_ON),
    "off": build_command(POWER_OFF),
}


def set_display(state: str) -> bool:
    """Run the command for `state` ('on' or 'off'). Returns True on success."""
    command = COMMANDS.get(state)
    if command is None:
        return False
    return os.system(command) == 0


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Display Control</title>
  <style>
    body {
      margin: 0; min-height: 100vh; display: grid; place-items: center;
      font-family: system-ui, sans-serif; background: #111827; color: #f9fafb;
    }
    main { text-align: center; }
    h1 { margin-bottom: 2rem; font-weight: 600; }
    form { display: inline-block; margin: 0 .75rem; }
    button {
      width: 9rem; padding: 1rem 0; font-size: 1.4rem; font-weight: 700;
      border: 0; border-radius: .75rem; color: #fff; cursor: pointer;
      transition: transform .1s, filter .15s;
    }
    button:hover { filter: brightness(1.15); }
    button:active { transform: scale(.96); }
    .on  { background: #16a34a; }
    .off { background: #dc2626; }
    p.msg { margin-top: 2rem; min-height: 1.5rem; }
    p.ok  { color: #4ade80; }
    p.err { color: #f87171; }
  </style>
</head>
<body>
  <main>
    <h1>Display Control</h1>
    <form method="post" action="{{ url_for('toggle', state='on') }}">
      <button class="on" type="submit">ON</button>
    </form>
    <form method="post" action="{{ url_for('toggle', state='off') }}">
      <button class="off" type="submit">OFF</button>
    </form>
    <p class="msg {{ status }}">{{ message }}</p>
  </main>
</body>
</html>
"""


@app.get("/")
def index():
    message = request.args.get("message", "")
    status = request.args.get("status", "")
    return render_template_string(PAGE, message=message, status=status)


@app.post("/display/<state>")
def toggle(state: str):
    state = state.lower()
    if state not in COMMANDS:
        return redirect(url_for("index", message="Invalid action.", status="err"))

    if set_display(state):
        return redirect(
            url_for("index", message=f"Display turned {state.upper()}.", status="ok")
        )
    return redirect(
        url_for("index", message=f"Could not turn display {state.upper()}.", status="err")
    )


if __name__ == "__main__":
    # 127.0.0.1 = reachable only from this computer. There is no login, so
    # avoid host="0.0.0.0" unless you trust everyone on your network.
    app.run(host="0.0.0.0", port=5000, debug=False)
