import pyautogui
import keyboard
import time

# Through this you can control your mouse with you numpad keys
# NOTE : The mouse also react to the keys at the main board which corresponds to the keys at the numpad

# You can edit values according to your needs
BASE_SPEED = 4
MAX_SPEED = 30
ACCELERATION = 1.5
SCROLL_AMOUNT = 200

speed = BASE_SPEED
dragging = False
enabled = False

fx = 0
fy = 0

# Scan codes
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

NUM_SLASH = 53
NUM_STAR = 55
NUM_MINUS = 74
NUM_PLUS = 78

blocked_keys = [
    NUM0, NUM1, NUM2, NUM3, NUM4,
    NUM5, NUM6, NUM7, NUM8, NUM9,
    NUM_SLASH, NUM_STAR, NUM_MINUS, NUM_PLUS
]


def block_keys():
    for key in blocked_keys:
        keyboard.block_key(key)


def unblock_keys():
    for key in blocked_keys:
        keyboard.unblock_key(key)


def toggle():
    global enabled
    enabled = not enabled

    if enabled:
        block_keys()
        print("Mouse Control: ON ",end="\r")
    else:
        unblock_keys()
        print("Mouse Control: OFF",end="\r")


keyboard.add_hotkey('scroll lock', toggle)
print("Press SCROLL LOCK to toggle ON/OFF")
while True:

    if not enabled:
        time.sleep(0.05)
        continue

    dx = 0
    dy = 0
    moving = False

    # Movement
    if keyboard.is_pressed(NUM8):
        dy -= 1
        moving = True

    if keyboard.is_pressed(NUM2):
        dy += 1
        moving = True

    if keyboard.is_pressed(NUM4):
        dx -= 1
        moving = True

    if keyboard.is_pressed(NUM6):
        dx += 1
        moving = True

    if keyboard.is_pressed(NUM7):
        dx -= 1
        dy -= 1
        moving = True

    if keyboard.is_pressed(NUM9):
        dx += 1
        dy -= 1
        moving = True

    if keyboard.is_pressed(NUM1):
        dx -= 1
        dy += 1
        moving = True

    if keyboard.is_pressed(NUM3):
        dx += 1
        dy += 1
        moving = True

    # Acceleration
    if moving:
        if speed < MAX_SPEED:
            speed += ACCELERATION
    else:
        speed = BASE_SPEED

    dx *= speed
    dy *= speed

    fx += dx
    fy += dy

    move_x = int(fx)
    move_y = int(fy)

    fx -= move_x
    fy -= move_y

    if move_x != 0 or move_y != 0:
        pyautogui.moveRel(move_x, move_y)

    # Left Click
    if keyboard.is_pressed(NUM5):
        pyautogui.click()
        time.sleep(0.2)

    # Right Click
    if keyboard.is_pressed(NUM0):
        pyautogui.rightClick()
        time.sleep(0.2)

    # Scroll
    if keyboard.is_pressed(NUM_PLUS):
        pyautogui.scroll(SCROLL_AMOUNT)

    if keyboard.is_pressed(NUM_MINUS):
        pyautogui.scroll(-SCROLL_AMOUNT)

    # Drag Start
    if keyboard.is_pressed(NUM_STAR) and not dragging:
        pyautogui.mouseDown()
        dragging = True
        time.sleep(0.2)

    # Drag End
    if keyboard.is_pressed(NUM_SLASH) and dragging:
        pyautogui.mouseUp()
        dragging = False
        time.sleep(0.2)

    time.sleep(0.005)

