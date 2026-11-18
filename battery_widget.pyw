"""
Laptop Battery Widget
A small, draggable battery widget built with Tkinter.

Install dependency:
    py -m pip install psutil

Run:
    py battery_widget.py
    (or rename to battery_widget.pyw / use pythonw.exe to avoid a console window)
"""

import tkinter as tk
from tkinter import messagebox
import psutil

BG = "#151922"
PANEL = "#202735"
TEXT = "#F2F5FA"
MUTED = "#9AA7B8"
GREEN = "#43D19E"
YELLOW = "#F2C15B"
RED = "#F06B72"
BLUE = "#72A7FF"


BAR_W = 236          # width of the progress bar in pixels
ALWAYS_ON_TOP = False  # set True to keep the widget above other windows

# Sentinel so the very first reading always renders.
_UNSET = object()


class BatteryWidget:
    REFRESH_MS = 5_000  # cheap to poll; makes plug/unplug show up quickly

    def __init__(self, root):
        self.root = root
        self.root.title("Battery Widget")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self.root.geometry("270x150+40+80")
        self.root.overrideredirect(True)
        if ALWAYS_ON_TOP:
            self.root.attributes("-topmost", True)

        self._drag_x = 0
        self._drag_y = 0
        self._last_state = _UNSET
        self._after_id = None

        self.frame = tk.Frame(root, bg=PANEL, padx=16, pady=12,
                              highlightthickness=1, highlightbackground="#303B4D")
        self.frame.pack(fill="both", expand=True)

        header = tk.Frame(self.frame, bg=PANEL)
        header.pack(fill="x")

        title = tk.Label(header, text="BATTERY", bg=PANEL, fg=MUTED,
                         font=("Segoe UI", 9, "bold"))
        title.pack(side="left")

        close = tk.Label(header, text="×", bg=PANEL, fg=MUTED,
                         font=("Segoe UI", 16), cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", lambda _event: self.close())

        self.percent_label = tk.Label(
            self.frame, text="--%", bg=PANEL, fg=TEXT,
            font=("Segoe UI", 25, "bold")
        )
        self.percent_label.pack(anchor="w", pady=(5, 2))

        # Canvas items are created once and only updated afterwards.
        self.canvas = tk.Canvas(self.frame, width=BAR_W, height=12,
                                bg=PANEL, highlightthickness=0)
        self.canvas.pack(anchor="w", pady=(1, 7))
        self.canvas.create_rectangle(0, 1, BAR_W, 11, fill="#354154", outline="")
        self.bar_fill = self.canvas.create_rectangle(0, 1, 0, 11,
                                                     fill=GREEN, outline="")

        self.status_label = tk.Label(
            self.frame, text="Reading battery status…", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 9)
        )
        self.status_label.pack(anchor="w")

        self.time_label = tk.Label(
            self.frame, text="", bg=PANEL, fg=MUTED,
            font=("Segoe UI", 8)
        )
        self.time_label.pack(anchor="w", pady=(2, 0))

        # Drag the widget by clicking and moving anywhere on its surface
        # (except the close button).
        for widget in (self.frame, header, title, self.percent_label,
                       self.canvas, self.status_label, self.time_label):
            widget.bind("<ButtonPress-1>", self.start_drag)
            widget.bind("<B1-Motion>", self.drag)

        self.update_battery()

    # ---------- window handling ----------

    def close(self):
        if self._after_id is not None:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.root.destroy()

    def start_drag(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def drag(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ---------- battery logic ----------

    @staticmethod
    def _read_state():
        """Return None (no battery) or (percent, plugged, minutes_left_or_None)."""
        battery = psutil.sensors_battery()
        if battery is None:
            return None

        percent = max(0, min(100, int(round(battery.percent))))

        secs = battery.secsleft
        if secs in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED) or secs < 0:
            minutes = None
        else:
            minutes = int(secs) // 60  # minute resolution avoids needless redraws

        return percent, bool(battery.power_plugged), minutes

    def update_battery(self):
        # try/finally guarantees the next refresh is always scheduled,
        # even if reading or rendering raises.
        try:
            state = self._read_state()
            if state != self._last_state:
                self._render(state)
                self._last_state = state
        except Exception as exc:
            self._last_state = _UNSET  # force a re-render on the next good read
            self.status_label.config(text=f"Error: {exc}"[:40])
        finally:
            self._after_id = self.root.after(self.REFRESH_MS, self.update_battery)

    def _render(self, state):
        if state is None:
            self.percent_label.config(text="N/A", fg=TEXT)
            self.status_label.config(text="Battery information unavailable")
            self.time_label.config(text="This device may not have a battery.")
            self.draw_bar(0, MUTED)
            return

        percent, plugged, minutes = state

        if plugged:
            status = "Plugged in · Charging" if percent < 100 else "Plugged in · Fully charged"
            color = BLUE
        else:
            status = "On battery power"
            if percent <= 20:
                color = RED
            elif percent <= 40:
                color = YELLOW
            else:
                color = GREEN

        self.percent_label.config(text=f"{percent}%", fg=color)
        self.status_label.config(text=status)
        self.draw_bar(percent, color)

        if minutes is not None:
            hours, mins = divmod(minutes, 60)
            self.time_label.config(text=f"Estimated time remaining: {hours}h {mins}m")
        elif plugged:
            self.time_label.config(text="Power adapter connected")
        else:
            self.time_label.config(text="Time estimate unavailable")

    def draw_bar(self, percent, color):
        self.canvas.coords(self.bar_fill, 0, 1, BAR_W * percent / 100, 11)
        self.canvas.itemconfig(self.bar_fill, fill=color)


if __name__ == "__main__":
    try:
        root = tk.Tk()
        BatteryWidget(root)
        root.mainloop()
    except Exception as exc:
        messagebox.showerror("Battery Widget", str(exc))
