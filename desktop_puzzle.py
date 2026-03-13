import tkinter as tk
import random
import mss
from PIL import Image, ImageTk
import ctypes

ROWS = 4
COLS = 6
SNAP_DISTANCE = 40

with mss.mss() as sct:
    monitor = sct.monitors[1]
    screen_w = monitor["width"]
    screen_h = monitor["height"]

piece_w = screen_w // COLS
piece_h = screen_h // ROWS

TOTAL_PIECES = ROWS * COLS
locked_count = 0

pieces = []
for r in range(ROWS):
    for c in range(COLS):
        pieces.append({
            "correct_x": c * piece_w,
            "correct_y": r * piece_h
        })

random.shuffle(pieces)

root = tk.Tk()
root.title("Live Desktop Puzzle")

root.attributes("-fullscreen", True)
root.attributes("-topmost", True)

root.bind("<Escape>", lambda e: "break")
root.bind("<Alt-F4>", lambda e: "break")

canvas = tk.Canvas(root, width=screen_w, height=screen_h, highlightthickness=0)
canvas.pack()

# --- EXCLUDE WINDOW FROM SCREEN CAPTURE ---
root.update()
hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
WDA_EXCLUDEFROMCAPTURE = 0x11
ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

items = {}
images = {}

for p in pieces:
    x = random.randint(0, screen_w - piece_w)
    y = random.randint(0, screen_h - piece_h)

    blank = Image.new("RGB", (piece_w, piece_h))
    tk_img = ImageTk.PhotoImage(blank)

    item = canvas.create_image(x, y, image=tk_img, anchor="nw")

    images[item] = tk_img
    items[item] = {
        "correct_x": p["correct_x"],
        "correct_y": p["correct_y"],
        "locked": False
    }

drag_data = {"item": None, "x": 0, "y": 0}


def update_tiles():

    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[1])

    frame = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

    for item in items:

        if items[item]["locked"]:
            continue

        cx = items[item]["correct_x"]
        cy = items[item]["correct_y"]

        piece = frame.crop((cx, cy, cx + piece_w, cy + piece_h))

        tk_img = ImageTk.PhotoImage(piece)
        images[item] = tk_img
        canvas.itemconfig(item, image=tk_img)

    root.after(120, update_tiles)


def on_press(event):
    item = canvas.find_closest(event.x, event.y)[0]

    if items[item]["locked"]:
        return

    canvas.tag_raise(item)

    drag_data["item"] = item
    drag_data["x"] = event.x
    drag_data["y"] = event.y


def on_drag(event):
    item = drag_data["item"]
    if item is None:
        return

    dx = event.x - drag_data["x"]
    dy = event.y - drag_data["y"]

    canvas.move(item, dx, dy)

    drag_data["x"] = event.x
    drag_data["y"] = event.y


def on_release(event):
    global locked_count

    item = drag_data["item"]
    if item is None:
        return

    x, y = canvas.coords(item)

    correct_x = items[item]["correct_x"]
    correct_y = items[item]["correct_y"]

    if abs(x - correct_x) < SNAP_DISTANCE and abs(y - correct_y) < SNAP_DISTANCE:

        canvas.coords(item, correct_x, correct_y)

        if not items[item]["locked"]:
            items[item]["locked"] = True
            locked_count += 1

        canvas.tag_lower(item)

        if locked_count == TOTAL_PIECES:
            root.destroy()

    drag_data["item"] = None


canvas.bind("<ButtonPress-1>", on_press)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_release)

update_tiles()

root.mainloop()