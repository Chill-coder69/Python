import sys
import ctypes
import winreg
from ctypes import wintypes
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout,
    QHBoxLayout, QLabel, QSlider, QCheckBox,
    QPushButton, QSystemTrayIcon, QMenu, QAction,
    QMessageBox, QGroupBox, QColorDialog
)

from PyQt5.QtCore import (
    Qt, QTimer, QSettings, QPointF, QSharedMemory
)

from PyQt5.QtGui import (
    QPainter, QColor, QPen, QIcon, QPixmap, QCursor
)


APP_NAME = "MouseGlow"
APP_VERSION = "2.1"

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# setting name: (minimum, maximum, default)
LIMITS = {
    "radius": (10, 100, 35),
    "opacity": (5, 255, 45),
    "border_width": (1, 8, 3),
    "border_opacity": (30, 255, 220),
}

LABELS = {
    "radius": "Circle Size",
    "opacity": "Fill Opacity",
    "border_width": "Border Thickness",
    "border_opacity": "Border Opacity",
}

DEFAULT_COLOR = "#ffdc00"

PRESET_COLORS = [
    "#ffdc00",  # yellow
    "#ff9500",  # orange
    "#ff3b30",  # red
    "#ff2d92",  # pink
    "#af52de",  # purple
    "#3a7bff",  # blue
    "#00c8ff",  # cyan
    "#34c759",  # green
]

# --------------------------------------------------
# Windows DPI configuration
# --------------------------------------------------

try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass


# --------------------------------------------------
# Keep-on-top support
# --------------------------------------------------

HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010

try:
    _set_window_pos = ctypes.windll.user32.SetWindowPos
    _set_window_pos.argtypes = [
        wintypes.HWND, wintypes.HWND,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.UINT
    ]
    _set_window_pos.restype = wintypes.BOOL
except Exception:
    _set_window_pos = None


def raise_topmost(widget):
    """Move the widget back to the top of the topmost windows
    without moving, resizing or activating it."""

    if _set_window_pos is None:
        return

    try:
        _set_window_pos(
            wintypes.HWND(int(widget.winId())),
            wintypes.HWND(HWND_TOPMOST),
            0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
        )
    except Exception:
        pass


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def read_setting(settings, key):
    """Read an int setting, falling back to the default if the
    stored value is missing, corrupt or out of range."""

    minimum, maximum, default = LIMITS[key]

    try:
        value = int(settings.value(key, default))
    except (TypeError, ValueError):
        value = default

    return max(minimum, min(maximum, value))


def read_color(settings):
    """Read the saved circle color, falling back to yellow."""

    color = QColor(str(settings.value("color", DEFAULT_COLOR)))

    if not color.isValid():
        color = QColor(DEFAULT_COLOR)

    return color


def make_icon():
    """Draw a small yellow circle to use as the tray icon."""

    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(255, 220, 0))
    painter.setPen(QPen(QColor(200, 150, 0), 2))
    painter.drawEllipse(3, 3, 26, 26)
    painter.end()

    return QIcon(pixmap)


def startup_command():
    """Command line that Windows should run at login."""

    if getattr(sys, "frozen", False):
        # Packaged .exe: run the executable itself.
        return f'"{sys.executable}"'

    executable = Path(sys.executable)

    # Prefer pythonw so no console window opens at login.
    pythonw = executable.with_name("pythonw.exe")

    if pythonw.exists():
        executable = pythonw

    script = Path(__file__).resolve()

    return f'"{executable}" "{script}"'


def is_startup_enabled():

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)

        # Only count it as enabled if it points at this program.
        return value == startup_command()

    except OSError:
        return False


# --------------------------------------------------
# Mouse highlight overlay
# --------------------------------------------------

class MouseOverlay(QWidget):
    """A small transparent window that follows the cursor.

    Only a window just big enough for the circle is moved around,
    instead of repainting one huge window covering every monitor.
    """

    def __init__(self, settings):
        super().__init__()

        self.settings = settings
        self.last_pos = None

        self.radius = read_setting(settings, "radius")
        self.opacity = read_setting(settings, "opacity")
        self.border_width = read_setting(settings, "border_width")
        self.border_opacity = read_setting(settings, "border_opacity")
        self.color = read_color(settings)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput |
            Qt.WindowDoesNotAcceptFocus
        )

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.apply_size()

        # Checks the cursor position. Only runs while enabled.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.follow_cursor)

        # Windows lets the taskbar and popup menus jump above other
        # topmost windows, so re-assert our position now and then.
        self.top_timer = QTimer(self)
        self.top_timer.timeout.connect(lambda: raise_topmost(self))

    def apply_size(self):

        size = 2 * (self.radius + self.border_width) + 4

        self.setFixedSize(size, size)

        # Force a reposition on the next check.
        self.last_pos = None

    def apply_settings(
        self, radius, opacity, border_width, border_opacity, color
    ):

        self.radius = radius
        self.opacity = opacity
        self.border_width = border_width
        self.border_opacity = border_opacity
        self.color = QColor(color)

        self.apply_size()
        self.follow_cursor()
        self.update()

    def follow_cursor(self):

        pos = QCursor.pos()

        # Skip all work if the cursor has not moved.
        if pos == self.last_pos:
            return

        self.last_pos = pos

        self.move(
            pos.x() - self.width() // 2,
            pos.y() - self.height() // 2
        )

    def start(self):

        self.last_pos = None
        self.follow_cursor()
        self.show()
        self.timer.start(16)
        self.top_timer.start(100)

    def stop(self):

        self.timer.stop()
        self.top_timer.stop()
        self.hide()

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        fill_color = QColor(self.color)
        fill_color.setAlpha(self.opacity)

        # The border is a slightly darker shade of the chosen color.
        border_color = self.color.darker(115)
        border_color.setAlpha(self.border_opacity)

        painter.setBrush(fill_color)
        painter.setPen(QPen(border_color, self.border_width))

        painter.drawEllipse(
            QPointF(self.width() / 2, self.height() / 2),
            self.radius,
            self.radius
        )

        painter.end()

    def cleanup(self):

        self.timer.stop()
        self.top_timer.stop()


# --------------------------------------------------
# Settings window
# --------------------------------------------------

class SettingsWindow(QDialog):

    def __init__(self, overlay, settings, parent=None):

        super().__init__(parent)

        self.overlay = overlay
        self.settings = settings
        self.sliders = {}
        self.color = QColor(overlay.color)

        self.setWindowTitle("MouseGlow Settings")
        self.setFixedWidth(390)

        self.setWindowFlags(
            self.windowFlags() | Qt.WindowStaysOnTopHint
        )

        # Saving to the registry on every slider tick is wasteful,
        # so wait until the slider has stopped moving.
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(400)
        self.save_timer.timeout.connect(self.save_settings)

        self.build_interface()

    def build_interface(self):

        main_layout = QVBoxLayout(self)

        title = QLabel("MouseGlow Settings")
        title.setStyleSheet("font-size: 21px; font-weight: bold;")

        subtitle = QLabel("Customize your mouse highlighting experience.")
        subtitle.setStyleSheet("color: gray;")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # Appearance settings.
        appearance = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout(appearance)

        for key in LIMITS:
            self.add_slider(appearance_layout, key)

        main_layout.addWidget(appearance)

        # Color settings.
        color_group = QGroupBox("Circle Color")
        color_layout = QVBoxLayout(color_group)

        presets_row = QHBoxLayout()

        for hex_value in PRESET_COLORS:
            button = QPushButton()
            button.setFixedSize(24, 24)
            button.setToolTip(hex_value)
            button.setStyleSheet(
                f"background-color: {hex_value};"
                "border: 1px solid #888;"
                "border-radius: 4px;"
            )
            button.clicked.connect(
                lambda _checked=False, c=hex_value:
                    self.set_color(QColor(c))
            )
            presets_row.addWidget(button)

        presets_row.addStretch()

        custom_button = QPushButton("Custom...")
        custom_button.clicked.connect(self.choose_custom_color)
        presets_row.addWidget(custom_button)

        color_layout.addLayout(presets_row)

        current_row = QHBoxLayout()

        self.color_swatch = QLabel()
        self.color_swatch.setFixedSize(24, 24)

        self.color_name = QLabel()

        current_row.addWidget(QLabel("Current:"))
        current_row.addWidget(self.color_swatch)
        current_row.addWidget(self.color_name)
        current_row.addStretch()

        color_layout.addLayout(current_row)

        self.update_color_preview()

        main_layout.addWidget(color_group)

        # Startup settings.
        startup_group = QGroupBox("Windows Startup")
        startup_layout = QVBoxLayout(startup_group)

        self.startup_checkbox = QCheckBox(
            "Start MouseGlow automatically with Windows"
        )

        self.startup_checkbox.setChecked(is_startup_enabled())
        self.startup_checkbox.toggled.connect(self.set_startup)

        startup_layout.addWidget(self.startup_checkbox)
        main_layout.addWidget(startup_group)

        # Hint.
        hint = QLabel(
            "Right-click the MouseGlow icon in the system tray\n"
            "to enable or disable highlighting, or to exit."
        )

        hint.setStyleSheet(
            "background: #eeeeee;"
            "padding: 12px;"
            "border-radius: 6px;"
        )

        main_layout.addWidget(hint)

        # Close button.
        close_button = QPushButton("Done")
        close_button.clicked.connect(self.close)

        main_layout.addWidget(close_button)

    def add_slider(self, layout, key):

        minimum, maximum, _ = LIMITS[key]
        initial = getattr(self.overlay, key)

        row = QHBoxLayout()

        label = QLabel(LABELS[key])
        value_label = QLabel(str(initial))
        value_label.setMinimumWidth(35)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(initial)

        row.addWidget(label)
        row.addStretch()
        row.addWidget(value_label)

        layout.addLayout(row)
        layout.addWidget(slider)

        # Connect after setting the initial value so it does not
        # trigger a needless save.
        slider.valueChanged.connect(
            lambda value, lbl=value_label: lbl.setText(str(value))
        )

        slider.valueChanged.connect(self.on_slider_changed)

        self.sliders[key] = slider

    def on_slider_changed(self, _value=None):

        self.overlay.apply_settings(
            self.sliders["radius"].value(),
            self.sliders["opacity"].value(),
            self.sliders["border_width"].value(),
            self.sliders["border_opacity"].value(),
            self.color
        )

        self.save_timer.start()

    def update_color_preview(self):

        self.color_swatch.setStyleSheet(
            f"background-color: {self.color.name()};"
            "border: 1px solid #888;"
            "border-radius: 4px;"
        )

        self.color_name.setText(self.color.name().upper())

    def set_color(self, color):

        self.color = QColor(color)
        self.update_color_preview()
        self.on_slider_changed()

    def choose_custom_color(self):

        chosen = QColorDialog.getColor(
            self.color,
            self,
            "Choose Circle Color"
        )

        # An invalid color means the dialog was cancelled.
        if chosen.isValid():
            self.set_color(chosen)

    def save_settings(self):

        for key, slider in self.sliders.items():
            self.settings.setValue(key, slider.value())

        self.settings.setValue("color", self.color.name())

    def closeEvent(self, event):

        # Make sure the latest values are saved.
        if self.save_timer.isActive():
            self.save_timer.stop()
            self.save_settings()

        super().closeEvent(event)

    # ----------------------------------------------
    # Windows startup registry management
    # ----------------------------------------------

    def set_startup(self, enabled):

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY,
                0,
                winreg.KEY_SET_VALUE
            ) as key:

                if enabled:
                    winreg.SetValueEx(
                        key,
                        APP_NAME,
                        0,
                        winreg.REG_SZ,
                        startup_command()
                    )
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass

        except OSError as error:

            QMessageBox.warning(
                self,
                "Startup Error",
                f"Unable to update startup settings:\n{error}"
            )

            # Put the checkbox back without re-triggering this method.
            self.startup_checkbox.blockSignals(True)
            self.startup_checkbox.setChecked(not enabled)
            self.startup_checkbox.blockSignals(False)


# --------------------------------------------------
# Main application
# --------------------------------------------------

class MouseGlow:

    def __init__(self):

        self.app = QApplication.instance()
        self.app.setQuitOnLastWindowClosed(False)

        self.settings = QSettings("MouseGlow", "MouseGlow")

        self.enabled = True

        self.overlay = MouseOverlay(self.settings)
        self.overlay.start()

        self.settings_window = SettingsWindow(
            self.overlay,
            self.settings
        )

        self.create_tray()

    def create_tray(self):

        self.tray = QSystemTrayIcon(make_icon())
        self.tray.setToolTip("MouseGlow - Mouse Highlighter")

        menu = QMenu()

        self.toggle_action = QAction("Disable Highlighting", menu)
        self.toggle_action.triggered.connect(self.toggle_highlighting)
        menu.addAction(self.toggle_action)

        settings_action = QAction("Settings...", menu)
        settings_action.triggered.connect(self.open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        exit_action = QAction("Exit MouseGlow", menu)
        exit_action.triggered.connect(self.quit)
        menu.addAction(exit_action)

        # Keep a reference so the menu is not garbage collected.
        self.tray_menu = menu

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_clicked)

        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        else:
            # Without a tray there would be no way to control the
            # program, so open the settings window instead.
            self.open_settings()

    def tray_clicked(self, reason):

        if reason == QSystemTrayIcon.DoubleClick:
            self.open_settings()

    def toggle_highlighting(self):

        self.enabled = not self.enabled

        if self.enabled:
            self.overlay.start()
            self.toggle_action.setText("Disable Highlighting")
        else:
            # Stops the timer too, so nothing runs while disabled.
            self.overlay.stop()
            self.toggle_action.setText("Enable Highlighting")

    def open_settings(self):

        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def quit(self):

        self.tray.hide()
        self.app.quit()


# --------------------------------------------------
# Application entry point
# --------------------------------------------------

if __name__ == "__main__":

    app = QApplication(sys.argv)

    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    # Allow only one copy of the program to run at a time.
    instance_guard = QSharedMemory(APP_NAME + "_single_instance")

    if instance_guard.attach() or not instance_guard.create(1):
        sys.exit(0)

    application = MouseGlow()

    app.aboutToQuit.connect(application.overlay.cleanup)

    sys.exit(app.exec_())
