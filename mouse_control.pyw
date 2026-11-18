"""
Control the mouse from the numeric keypad.

Run it, then press the Del key on the numeric keypad (it types "." while
NumLock is ON) to switch mouse control ON / OFF.
Press F8 to quit.  Keep NumLock ON.

A small circle in the top-right corner of the screen shows the state:
RED = control is OFF, GREEN = control is ON.  Drag it with the mouse to move it.
(If tkinter or a display is not available the program runs without the circle.)

Design notes
------------
* All key handling happens in ONE keyboard hook.  It only touches shared state
  (under a lock); every pyautogui call is made from a single worker thread.
* The tkinter window runs in the main thread (tkinter requires that) and only
  READS the shared state, polling it a few times per second.
* Keypad keys are recognised by scan code AND `event.is_keypad`, so the real
  arrow / Home / End / PgUp / PgDn / Insert keys are never captured or blocked.
* Movement is time based (pixels per second), so it does not depend on how
  fast the loop happens to run, and diagonals are normalised.
* Clicks / drag start / drag end fire once per key press (no auto-repeat, no
  blocking sleeps); scroll and volume repeat on a timer instead of sleeping.
* Everything is cleaned up on exit: mouse button released, hook removed.
"""

import math
import sys
import threading
import time
import traceback
from collections import deque

import keyboard
import pyautogui

try:
    import tkinter as tk
except ImportError:          # tkinter is optional: only the status circle needs it
    tk = None

# ------------------------------------------------------------------ settings
# Speeds are in pixels per second (the old values were "pixels per loop
# iteration", which made the real speed depend on the loop rate).
BASE_SPEED = 100.0        # px/s when a movement key is first pressed
MAX_SPEED = 1000.0        # px/s top speed
ACCELERATION = 900.0      # px/s gained per second while a movement key is held

SCROLL_AMOUNT = 200       # passed to pyautogui.scroll() on every scroll step
SCROLL_INTERVAL = 0.05    # seconds between scroll steps while the key is held
VOLUME_INTERVAL = 0.10    # seconds between volume steps while the key is held

TICK = 0.008              # control-loop period while control is ON
IDLE_TICK = 0.05          # control-loop period while control is OFF
MAX_DT = 0.05             # cap on one time step (protects against stalls)

EXIT_KEY = "f8"           # the ON/OFF toggle is the numpad Del key, see TOGGLE_CODE below

# Status circle
SHOW_INDICATOR = True     # set to False to run without the window
INDICATOR_SIZE = 22       # window size in pixels
INDICATOR_MARGIN = 16     # distance from the top-right corner of the screen
INDICATOR_POLL_MS = 50    # how often the window checks the state
COLOR_ON = "#2ecc40"      # green
COLOR_OFF = "#e53935"     # red
COLOR_OUTLINE = "#ffffff"
# Windows can make this colour see-through so only the circle is visible.
# Other systems get a small dark badge behind the circle instead.
TRANSPARENT_COLOR = "#010203"
FALLBACK_BACKGROUND = "#202020"

# Keep pyautogui from sleeping after every call, and disable its corner
# fail-safe (moving the cursor into a screen corner would otherwise raise
# FailSafeException and kill the program).  F8 is the escape hatch instead.
pyautogui.PAUSE = 0.005
pyautogui.FAILSAFE = False

# ---------------------------------------------------------------- scan codes
NUM0 = 82
NUM1 = 79
NUM2 = 80
NUM3 = 81
NUM4 = 75
NUM5 = 76
NUM6 = 77
NUM7 = 71
NUM8 = 72
NUM9 = 73
NUM_MINUS = 74
NUM_PLUS = 78
NUM_DEL = 83              # numpad Del / "." key (the real Delete key shares this code)

# The key that switches control ON/OFF. It is matched together with
# `is_keypad`, so the separate Delete key in the navigation block is not affected.
TOGGLE_CODE = NUM_DEL

KEYPAD_CODES = frozenset({
    NUM0, NUM1, NUM2, NUM3, NUM4, NUM5,
    NUM6, NUM7, NUM8, NUM9, NUM_MINUS, NUM_PLUS,
})

# Keys that trigger exactly once per physical press.
PRESS_ACTIONS = {
    NUM5: "left_click",
    NUM0: "right_click",
    NUM7: "drag_start",
    NUM1: "drag_end",
}

CONTROLS = """>>>>>>> Controls
 NUM 8 - UP
 NUM 2 - DOWN
 NUM 4 - LEFT
 NUM 6 - RIGHT
 NUM 5 - LEFT CLICK
 NUM 0 - RIGHT CLICK
 NUM 9 - SCROLL UP
 NUM 3 - SCROLL DOWN
 NUM 7 - DRAG START
 NUM 1 - DRAG END
 NUM + - VOLUME UP
 NUM - - VOLUME DOWN
>>>>>>> NUM DEL (the Del / . key) toggles control ON/OFF, F8 exits (keep NumLock ON)
>>>>>>> Status circle: RED = OFF, GREEN = ON (drag it to move it)
"""

STATUS_ON = "Mouse Control: ON "
STATUS_OFF = "Mouse Control: OFF"


def show_status(enabled):
    print(STATUS_ON if enabled else STATUS_OFF, end="\r", flush=True)


# ------------------------------------------------------------- shared state
class SharedState:
    """State shared between the keyboard-hook thread, the control loop and the GUI."""

    def __init__(self):
        self.lock = threading.Lock()
        self.enabled = False
        self.held = set()        # keypad scan codes currently held (captured)
        self.swallowed = set()   # presses we suppressed -> suppress their release
        self.passed = set()      # presses we let through -> let their release through
        self.actions = deque()   # (name, argument) work for the control loop
        self.quit = threading.Event()
        self._toggle_down = False

    def handle_event(self, event):
        """Keyboard hook body. Return True to pass the event on, False to block it."""
        is_down = event.event_type == keyboard.KEY_DOWN

        # Toggle key: the NUMPAD Del key (is_keypad True). The separate Delete key
        # has the same scan code but is_keypad False, so it is left alone.
        # It is always swallowed, otherwise a "." would be typed into the
        # focused window every time you toggle.
        if event.is_keypad and event.scan_code == TOGGLE_CODE:
            with self.lock:
                if not is_down:
                    self._toggle_down = False
                elif not self._toggle_down:      # ignore auto-repeat
                    self._toggle_down = True
                    self.enabled = not self.enabled
                    self.held.clear()
                    self.actions.append(("state", self.enabled))
            return False

        if event.name == EXIT_KEY:
            if is_down:
                self.quit.set()
            return True

        # Only the numeric keypad is ever captured. Real arrow / navigation
        # keys share these scan codes but have is_keypad == False.
        if not (event.is_keypad and event.scan_code in KEYPAD_CODES):
            return True

        code = event.scan_code
        with self.lock:
            if not is_down:
                self.held.discard(code)
                self.passed.discard(code)
                if code in self.swallowed:
                    self.swallowed.discard(code)
                    return False
                return True

            # Key down (this includes OS auto-repeat).
            if code in self.swallowed:
                return False                     # repeat of a captured press
            if code in self.passed or not self.enabled:
                # Pressed while OFF (or before we were enabled): leave it alone
                # for its whole press/release cycle.
                self.passed.add(code)
                return True

            self.swallowed.add(code)
            self.held.add(code)
            action = PRESS_ACTIONS.get(code)
            if action:
                self.actions.append((action, None))
            return False

    def snapshot(self):
        """Atomically fetch (enabled, held keys, pending actions)."""
        with self.lock:
            actions = list(self.actions)
            self.actions.clear()
            return self.enabled, frozenset(self.held), actions


def make_hook(state):
    def on_key(event):
        try:
            return state.handle_event(event)
        except Exception:
            return True      # fail open: never trap the user's keyboard
    return on_key


# ---------------------------------------------------------- mouse controller
class MouseController:
    """Performs all mouse / volume actions. Used from one thread only."""

    def __init__(self):
        self.speed = BASE_SPEED
        self.fx = 0.0
        self.fy = 0.0
        self.dragging = False
        self.next_scroll = 0.0
        self.next_volume = 0.0

    def reset_motion(self):
        self.speed = BASE_SPEED
        self.fx = 0.0
        self.fy = 0.0

    def release_drag(self):
        if self.dragging:
            pyautogui.mouseUp()
            self.dragging = False

    def handle_action(self, name, arg):
        if name == "state":
            if not arg:                       # switched OFF
                self.release_drag()
            self.reset_motion()
            show_status(arg)
        elif name == "left_click":
            # A click would press+release the button and silently end a drag.
            if not self.dragging:
                pyautogui.click()
        elif name == "right_click":
            pyautogui.rightClick()
        elif name == "drag_start":
            if not self.dragging:
                pyautogui.mouseDown()
                self.dragging = True
        elif name == "drag_end":
            self.release_drag()

    def update(self, now, dt, held):
        self._move(dt, held)

        scroll_dir = (NUM9 in held) - (NUM3 in held)
        if scroll_dir and now >= self.next_scroll:
            pyautogui.scroll(SCROLL_AMOUNT * scroll_dir)
            self.next_scroll = now + SCROLL_INTERVAL

        volume_dir = (NUM_PLUS in held) - (NUM_MINUS in held)
        if volume_dir and now >= self.next_volume:
            pyautogui.press("volumeup" if volume_dir > 0 else "volumedown")
            self.next_volume = now + VOLUME_INTERVAL

    def _move(self, dt, held):
        dx = (NUM6 in held) - (NUM4 in held)
        dy = (NUM2 in held) - (NUM8 in held)
        if dx == 0 and dy == 0:
            self.reset_motion()
            return

        self.speed = min(MAX_SPEED, self.speed + ACCELERATION * dt)
        # Normalising keeps diagonal movement at the same speed as straight.
        scale = self.speed * dt / math.hypot(dx, dy)
        self.fx += dx * scale
        self.fy += dy * scale

        move_x = int(self.fx)
        move_y = int(self.fy)
        self.fx -= move_x                         # keep the sub-pixel remainder
        self.fy -= move_y
        if move_x or move_y:
            pyautogui.moveRel(move_x, move_y)


def control_loop(state, controller):
    """Worker thread: turns captured key state into mouse actions."""
    try:
        last = time.perf_counter()
        while not state.quit.is_set():
            now = time.perf_counter()
            dt = min(now - last, MAX_DT)
            last = now

            enabled, held, actions = state.snapshot()
            for name, arg in actions:
                controller.handle_action(name, arg)
            if enabled:
                controller.update(now, dt, held)

            state.quit.wait(TICK if enabled else IDLE_TICK)
    finally:
        state.quit.set()              # if this thread dies, shut everything down
        controller.release_drag()     # never leave the mouse button held down


# ----------------------------------------------------------- status circle
class StatusIndicator:
    """A tiny always-on-top circle: red while control is OFF, green while ON.

    Must be created and run in the main thread (a tkinter requirement). It only
    reads `state`, so it needs no locking.
    """

    def __init__(self, state):
        self.state = state
        self._shown = None
        self._drag_dx = 0
        self._drag_dy = 0

        root = tk.Tk()                       # raises tk.TclError without a display
        self.root = root
        root.title("Mouse Control")
        root.overrideredirect(True)          # no title bar / border / taskbar entry
        root.attributes("-topmost", True)    # stay above other windows

        background = FALLBACK_BACKGROUND
        if sys.platform.startswith("win"):
            root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
            background = TRANSPARENT_COLOR

        x = root.winfo_screenwidth() - INDICATOR_SIZE - INDICATOR_MARGIN
        root.geometry(f"{INDICATOR_SIZE}x{INDICATOR_SIZE}+{x}+{INDICATOR_MARGIN}")

        canvas = tk.Canvas(root, width=INDICATOR_SIZE, height=INDICATOR_SIZE,
                           bg=background, highlightthickness=0, bd=0)
        canvas.pack()
        self.canvas = canvas
        pad = 2
        self._circle = canvas.create_oval(
            pad, pad, INDICATOR_SIZE - pad, INDICATOR_SIZE - pad,
            fill=COLOR_OFF, outline=COLOR_OUTLINE, width=1)

        canvas.bind("<ButtonPress-1>", self._start_drag)
        canvas.bind("<B1-Motion>", self._drag)

        # Ctrl+C inside a Tk callback would otherwise just print a traceback.
        root.report_callback_exception = self._on_callback_error

        self._paint(state.enabled)
        root.after(INDICATOR_POLL_MS, self._poll)

    def run(self):
        """Block until the program quits."""
        self.root.mainloop()

    def _paint(self, enabled):
        self.canvas.itemconfigure(self._circle, fill=COLOR_ON if enabled else COLOR_OFF)
        self._shown = enabled

    def _poll(self):
        if self.state.quit.is_set():
            self.root.destroy()              # ends mainloop()
            return
        enabled = self.state.enabled
        if enabled != self._shown:
            self._paint(enabled)
        self.root.after(INDICATOR_POLL_MS, self._poll)

    def _start_drag(self, event):
        self._drag_dx = event.x
        self._drag_dy = event.y

    def _drag(self, event):
        self.root.geometry(f"+{event.x_root - self._drag_dx}+{event.y_root - self._drag_dy}")

    def _on_callback_error(self, exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            self.state.quit.set()
        else:
            traceback.print_exception(exc_type, exc, tb)


def create_indicator(state):
    """Return a StatusIndicator, or None if it is disabled / unavailable."""
    if not SHOW_INDICATOR:
        return None
    if tk is None:
        print("tkinter is not installed - running without the status circle.")
        return None
    try:
        return StatusIndicator(state)
    except tk.TclError as exc:
        print(f"Could not open the status circle ({exc}) - running without it.")
        return None


def wait_until_quit(state):
    """Block the main thread (without a GUI) while staying responsive to Ctrl+C."""
    while not state.quit.wait(0.2):
        pass


# ---------------------------------------------------------------------- main
def main():
    state = SharedState()
    controller = MouseController()

    print(CONTROLS)
    indicator = create_indicator(state)   # before the hook, so a failure leaves nothing behind
    show_status(False)

    keyboard.hook(make_hook(state), suppress=True)
    worker = threading.Thread(target=control_loop, args=(state, controller),
                              name="mouse-control", daemon=True)
    try:
        worker.start()
        if indicator is not None:
            indicator.run()               # returns when state.quit is set
        else:
            wait_until_quit(state)
    except KeyboardInterrupt:
        pass
    finally:
        state.quit.set()
        worker.join(timeout=2)            # the worker releases any held mouse button
        keyboard.unhook_all()             # removes the hook -> keys work normally again
        print("\nMouse Control: EXITED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
