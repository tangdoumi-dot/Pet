from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parent
BASE = ROOT / "decoded" / "base.png"
FRAMES = ROOT / "frames"
FINAL = ROOT / "final"
QA = ROOT / "qa"
CELL_W = 192
CELL_H = 208
ATLAS_W = CELL_W * 8
ATLAS_H = CELL_H * 9

ROWS = [
    ("idle", 0, 6),
    ("happy", 1, 8),
    ("shy", 2, 8),
    ("cry", 3, 4),
    ("surprised", 4, 5),
    ("clicked", 5, 8),
    ("drag", 6, 6),
    ("sleep", 7, 6),
    ("study", 8, 6),
]


def clear_dirs() -> None:
    for path in (FRAMES, FINAL, QA):
        path.mkdir(parents=True, exist_ok=True)
    for item in FRAMES.glob("**/*"):
        if item.is_file():
            item.unlink()


def cutout_base() -> Image.Image:
    src = Image.open(BASE).convert("RGBA")
    pixels = src.load()
    w, h = src.size
    visited = set()
    stack = []

    def is_key(x: int, y: int) -> bool:
        r, g, b, _a = pixels[x, y]
        return g > 165 and b > 165 and r < 95 and abs(g - b) < 45

    for x in range(w):
        if is_key(x, 0):
            stack.append((x, 0))
        if is_key(x, h - 1):
            stack.append((x, h - 1))
    for y in range(h):
        if is_key(0, y):
            stack.append((0, y))
        if is_key(w - 1, y):
            stack.append((w - 1, y))

    while stack:
        x, y = stack.pop()
        if (x, y) in visited or not (0 <= x < w and 0 <= y < h) or not is_key(x, y):
            continue
        visited.add((x, y))
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    alpha = Image.new("L", src.size, 255)
    ad = alpha.load()
    for x, y in visited:
        ad[x, y] = 0
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.35))
    src.putalpha(alpha)
    bbox = src.getbbox()
    if not bbox:
        raise RuntimeError("base cutout is empty")
    cutout = src.crop(bbox)
    cutout.thumbnail((164, 196), Image.Resampling.LANCZOS)
    return cutout


def draw_face(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], mood: str, frame: int) -> None:
    x, y, w, h = box
    cx = x + w // 2
    eye_y = y + int(h * 0.235)
    mouth_y = y + int(h * 0.305)
    skin = (248, 216, 194, 235)
    dark = (69, 45, 41, 255)
    gold = (234, 154, 39, 255)
    blush = (255, 145, 150, 130)

    def cover_eyes() -> None:
        draw.rounded_rectangle((cx - 45, eye_y - 13, cx - 14, eye_y + 15), radius=7, fill=skin)
        draw.rounded_rectangle((cx + 12, eye_y - 13, cx + 43, eye_y + 15), radius=7, fill=skin)

    if mood in {"happy", "clicked"}:
        cover_eyes()
        draw.arc((cx - 39, eye_y - 8, cx - 18, eye_y + 7), 0, 180, fill=dark, width=3)
        draw.arc((cx + 14, eye_y - 8, cx + 35, eye_y + 7), 0, 180, fill=dark, width=3)
        draw.arc((cx - 9, mouth_y - 1, cx + 10, mouth_y + 8), 0, 180, fill=(185, 92, 78, 255), width=2)
    elif mood == "shy":
        cover_eyes()
        draw.line((cx - 37, eye_y + 3, cx - 20, eye_y + 7), fill=dark, width=3)
        draw.line((cx + 18, eye_y + 7, cx + 35, eye_y + 3), fill=dark, width=3)
        draw.ellipse((cx - 52, eye_y + 16, cx - 33, eye_y + 25), fill=blush)
        draw.ellipse((cx + 30, eye_y + 16, cx + 49, eye_y + 25), fill=blush)
    elif mood == "cry":
        draw.ellipse((cx - 39, eye_y - 7, cx - 20, eye_y + 13), fill=gold, outline=dark, width=2)
        draw.ellipse((cx + 17, eye_y - 7, cx + 36, eye_y + 13), fill=gold, outline=dark, width=2)
        draw.line((cx - 31, eye_y + 13, cx - 35, eye_y + 28), fill=(116, 200, 255, 230), width=3)
        draw.arc((cx - 8, mouth_y + 5, cx + 8, mouth_y + 17), 180, 360, fill=(185, 92, 78, 255), width=2)
    elif mood == "surprised":
        draw.ellipse((cx - 40, eye_y - 9, cx - 20, eye_y + 12), fill=gold, outline=dark, width=2)
        draw.ellipse((cx + 18, eye_y - 9, cx + 38, eye_y + 12), fill=gold, outline=dark, width=2)
        draw.ellipse((cx - 4, mouth_y + 2, cx + 5, mouth_y + 11), fill=(166, 80, 72, 240))
    elif mood == "sleep":
        cover_eyes()
        draw.line((cx - 41, eye_y + 2, cx - 20, eye_y + 2), fill=dark, width=3)
        draw.line((cx + 17, eye_y + 2, cx + 38, eye_y + 2), fill=dark, width=3)
    elif mood == "blink":
        cover_eyes()
        draw.line((cx - 39, eye_y + 2, cx - 21, eye_y + 2), fill=dark, width=3)
        draw.line((cx + 18, eye_y + 2, cx + 36, eye_y + 2), fill=dark, width=3)


def draw_effects(draw: ImageDraw.ImageDraw, mood: str, box: tuple[int, int, int, int], frame: int) -> None:
    x, y, w, h = box
    cx = x + w // 2
    if mood == "drag":
        glove = (39, 36, 35, 255)
        sleeve = (52, 75, 84, 255)
        left_hand = (x + 14, y + 112, x + 31, y + 128)
        right_hand = (x + w - 31, y + 112, x + w - 14, y + 128)
        draw.line((x + 44, y + 135, x + 24, y + 123), fill=sleeve, width=5)
        draw.line((x + w - 44, y + 135, x + w - 24, y + 123), fill=sleeve, width=5)
        draw.rounded_rectangle(left_hand, radius=4, fill=glove)
        draw.rounded_rectangle(right_hand, radius=4, fill=glove)
    elif mood == "sleep":
        color = (91, 104, 126, 220)
        ox = 126 + (frame % 3) * 3
        oy = 35 - (frame % 3) * 2
        draw.text((ox, oy), "z", fill=color)
        draw.text((ox + 9, oy - 8), "z", fill=color)
        draw.text((ox + 20, oy - 17), "z", fill=color)
    elif mood == "study":
        cover = (82, 68, 50, 255)
        pages = (238, 226, 198, 255)
        top = y + int(h * 0.61)
        draw.polygon([(cx - 43, top), (cx - 5, top + 10), (cx - 5, top + 46), (cx - 45, top + 36)], fill=pages)
        draw.polygon([(cx + 5, top + 10), (cx + 43, top), (cx + 45, top + 36), (cx + 5, top + 46)], fill=pages)
        draw.line((cx, top + 8, cx, top + 47), fill=cover, width=3)
        draw.line((cx - 43, top, cx - 5, top + 10), fill=cover, width=3)
        draw.line((cx + 5, top + 10, cx + 43, top), fill=cover, width=3)


def make_frame(sprite: Image.Image, mood: str, i: int, n: int) -> Image.Image:
    frame = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    bob = {
        "idle": [0, -1, -2, -1, 0, 1],
        "happy": [0, -1, -1, 0, 1, 0, -1, 0],
        "shy": [0, 1, 2, 1, 0, 1, 2, 1],
        "cry": [0, 1, 0, 1],
        "surprised": [0, -2, -1, 0, 1],
        "clicked": [0, -1, -2, -1, 0, 1, 0, -1],
        "drag": [-4, -5, -6, -5, -4, -5],
        "sleep": [0, 1, 2, 1, 0, 1],
        "study": [0, 0, 1, 1, 0, 0],
    }[mood][i]
    lean = 0
    if mood == "shy":
        lean = [-2, -1, 0, 1, 2, 1, 0, -1][i]
    elif mood == "drag":
        lean = [-2, 1, -1, 2, -1, 1][i]
    elif mood == "study":
        lean = [0, 0, 1, 1, 0, -1][i]

    work = sprite
    if lean:
        work = sprite.rotate(lean, resample=Image.Resampling.BICUBIC, expand=True)
    x = (CELL_W - work.width) // 2
    y = CELL_H - work.height - 6 + bob
    if mood == "sleep":
        y += 6
    frame.alpha_composite(work, (x, y))
    draw = ImageDraw.Draw(frame, "RGBA")
    box = (x, y, work.width, work.height)
    face_mood = mood
    if mood == "idle" and i == 3:
        face_mood = "blink"
    if mood == "study":
        face_mood = "idle"
    draw_face(draw, box, face_mood, i)
    draw_effects(draw, mood, box, i)
    return frame


def write_outputs() -> None:
    clear_dirs()
    sprite = cutout_base()
    atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (0, 0, 0, 0))
    manifest = {"rows": []}
    for state, row, count in ROWS:
        state_dir = FRAMES / state
        state_dir.mkdir(parents=True, exist_ok=True)
        manifest["rows"].append({"state": state, "row": row, "frames": count})
        for i in range(count):
            frame = make_frame(sprite, state, i, count)
            path = state_dir / f"{i:02d}.png"
            frame.save(path)
            atlas.alpha_composite(frame, (i * CELL_W, row * CELL_H))
    FINAL.mkdir(exist_ok=True)
    atlas.save(FINAL / "spritesheet.png")
    atlas.save(FINAL / "spritesheet.webp", format="WEBP", lossless=True, quality=100, method=6, exact=True)
    (FRAMES / "frames-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    write_outputs()
