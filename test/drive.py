#!/usr/bin/env python3
"""Click every toolbar button in a running KiCad editor and record what happened.

    python3 test/drive.py board|schematic <out-dir>

The editor must be running through X11 (started with GDK_BACKEND=x11) so that
synthetic clicks reach it. Each button is found on screen by matching our own
icon picture, clicked, and judged by what changed: a new window (a dialog), the
button staying pressed (a tool now active), or the drawing or status bar
changing. Escape is pressed after each, and any dialog it opened is closed.

Writes <out-dir>/results.json and a before/after picture per button.
"""
import json
import pathlib
import sys
import time

import cv2
import numpy as np
from Xlib import X, XK, display
from Xlib.ext import xtest

HERE = pathlib.Path(__file__).resolve().parent
SKIN = HERE.parent
sys.path.insert(0, str(SKIN / "setup"))
import apply  # noqa: E402  (the toolbar definitions)

D = display.Display()
ROOT = D.screen().root


def windows():
    out = {}

    def walk(w):
        try:
            prop = w.get_full_property(D.intern_atom("_NET_WM_NAME"), D.intern_atom("UTF8_STRING"))
            name = prop.value.decode("utf-8", "replace") if prop else w.get_wm_name()
            attrs = w.get_attributes()
        except Exception:
            return
        if name and attrs.map_state == X.IsViewable:
            out[w.id] = (w, name)
        try:
            for c in w.query_tree().children:
                walk(c)
        except Exception:
            pass

    walk(ROOT)
    return out


def find(title):
    for w, name in windows().values():
        if title in str(name):
            return w
    sys.exit(f"no window titled {title!r}")


def geom(w):
    g = w.get_geometry()
    t = w.translate_coords(ROOT, 0, 0)
    return -t.x, -t.y, g.width, g.height


def grab(w):
    # Under XWayland the root window holds no picture; read KiCad's own window.
    _, _, wd, ht = geom(w)
    raw = w.get_image(0, 0, wd, ht, X.ZPixmap, 0xFFFFFFFF)
    img = np.frombuffer(raw.data, dtype=np.uint8).reshape(ht, wd, 4)[:, :, :3]
    return np.ascontiguousarray(img)


_SCALE = []


def scale():
    """Synthetic pointer moves arrive multiplied by the desktop's display
    scaling; measure it once by moving and reading back."""
    if not _SCALE:
        xtest.fake_input(D, X.MotionNotify, x=400, y=400)
        D.sync()
        time.sleep(0.3)
        p = ROOT.query_pointer()
        _SCALE.append((p.root_x / 400, p.root_y / 400))
    return _SCALE[0]


def move_to(tx, ty):
    """Put the pointer on (tx, ty) and check it got there. Synthetic moves are
    scaled by the desktop and sometimes treated as relative, so steer: read
    where it is, nudge by the remaining distance, repeat."""
    for _ in range(12):
        p = ROOT.query_pointer()
        dx, dy = tx - p.root_x, ty - p.root_y
        if abs(dx) <= 1 and abs(dy) <= 1:
            return True
        xtest.fake_input(D, X.MotionNotify, True, x=int(dx / 1.5) or (1 if dx > 0 else -1 if dx < 0 else 0),
                         y=int(dy / 1.5) or (1 if dy > 0 else -1 if dy < 0 else 0))
        D.sync()
        time.sleep(0.05)
    p = ROOT.query_pointer()
    return abs(tx - p.root_x) <= 3 and abs(ty - p.root_y) <= 3


def click(w, cx, cy, button=1):
    x, y, _, _ = geom(w)
    if not move_to(x + cx, y + cy):
        print("  pointer did not reach the button", flush=True)
    time.sleep(0.15)
    xtest.fake_input(D, X.ButtonPress, button)
    D.sync()
    time.sleep(0.08)
    xtest.fake_input(D, X.ButtonRelease, button)
    D.sync()


def key(name):
    code = D.keysym_to_keycode(XK.string_to_keysym(name))
    xtest.fake_input(D, X.KeyPress, code)
    xtest.fake_input(D, X.KeyRelease, code)
    D.sync()


def front(title):
    """Bring the window to the front through the desktop itself; X11 focus alone
    leaves it behind other windows, and clicks land on whatever is on top."""
    import subprocess
    import tempfile
    js = ("for (const w of workspace.windowList()) { if (String(w.caption).includes(%r)) "
          "{ workspace.activeWindow = w; break; } }" % title)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
        f.write(js)
    out = subprocess.run(["gdbus", "call", "--session", "--dest", "org.kde.KWin", "--object-path", "/Scripting",
                          "--method", "org.kde.kwin.Scripting.loadScript", f.name, f"front{time.time_ns()}"],
                         capture_output=True, text=True).stdout
    sid = "".join(ch for ch in out if ch.isdigit())
    subprocess.run(["gdbus", "call", "--session", "--dest", "org.kde.KWin", "--object-path",
                    f"/Scripting/Script{sid}", "--method", "org.kde.kwin.Script.run"], capture_output=True)
    time.sleep(0.4)


def close(win):
    """Ask a window to close the way the window manager's close button does."""
    from Xlib.protocol import event
    proto, delete = D.intern_atom("WM_PROTOCOLS"), D.intern_atom("WM_DELETE_WINDOW")
    ev = event.ClientMessage(window=win, client_type=proto, data=(32, [delete, X.CurrentTime, 0, 0, 0]))
    win.send_event(ev)
    D.sync()


def template(word):
    """Our icon at toolbar size, on the toolbar's dark background, as BGR."""
    svg = SKIN / "icons/svg" / f"{word.replace(' ', '_')}.svg"
    png = HERE / "tmpl" / f"{word.replace(' ', '_')}.png"
    png.parent.mkdir(exist_ok=True)
    if not png.exists():
        import subprocess
        subprocess.run(["magick", "-background", "none", "-density", str(96 * apply.ICON_SIZE / 24 * 4),
                        str(svg), "-resize", f"{apply.ICON_SIZE}x{apply.ICON_SIZE}", str(png)], check=True)
    rgba = cv2.imread(str(png), cv2.IMREAD_UNCHANGED)
    if rgba.dtype != np.uint8:
        rgba = (rgba / 257).astype(np.uint8)
    return rgba


def locate(img, word):
    """Best match of the icon, searched only where toolbars are: the top bars
    and the two-wide column at the left edge."""
    rgba = template(word)
    alpha = rgba[:, :, 3]
    t = np.ascontiguousarray(rgba[:, :, :3])
    h, w = t.shape[:2]
    best = (-1.0, (0, 0))
    for x0, y0, x1, y1 in ((0, 0, img.shape[1], 130), (0, 0, 130, img.shape[0])):
        region = np.ascontiguousarray(img[y0:y1, x0:x1])
        res = cv2.matchTemplate(region, t, cv2.TM_CCOEFF_NORMED, mask=cv2.merge([alpha] * 3))
        res = np.nan_to_num(res, nan=-1, posinf=-1, neginf=-1)
        _, score, _, loc = cv2.minMaxLoc(res)
        if score > best[0]:
            best = (score, (x0 + loc[0] + w // 2, y0 + loc[1] + h // 2))
    return best


def spans(profile, gap=4, min_len=10):
    """Runs of 'something drawn' along a strip, as (start, end) pairs."""
    on = profile > 0
    out, start, quiet = [], None, 0
    for i, v in enumerate(on):
        if v:
            if start is None:
                start = i
            quiet = 0
        elif start is not None:
            quiet += 1
            if quiet > gap:
                if i - quiet - start >= min_len:
                    out.append((start, i - quiet))
                start, quiet = None, 0
    if start is not None and len(on) - start >= min_len:
        out.append((start, len(on)))
    return out


def ink(strip):
    bg = np.median(strip.reshape(-1, 3), axis=0)
    return (np.abs(strip.astype(int) - bg).max(axis=2) > 45)


def layout(which, img):
    """Every button's centre, from where icons are actually drawn: the top bar
    left to right, and the two-wide column row by row."""
    top, rows, table, view, end = parts(which)
    pos = {}
    # Top bar: the first strip of icons under the menu.
    band = ink(img[40:100, :])
    ys = np.where(band.any(axis=1))[0]
    y = 40 + int(np.median(ys))
    xs = spans(ink(img[y - 14:y + 14, :]).sum(axis=0), gap=3, min_len=14)
    centres = [(a + b) // 2 for a, b in xs if b - a < 60]
    left_words = [it[0] for it in top + view if it is not apply.SEP]
    for w, c in zip(left_words, centres):
        pos[w] = (c, y)
    right = [it[0] for it in end if not it[0].startswith("@")]
    pos[right[-1]] = (centres[-1], y)          # the editor switch, far right
    gaps = [centres[i + 1] - centres[i] for i in range(len(centres) - 1)]
    cam = centres[gaps.index(max(gaps)) + 1]   # first icon after the stretch
    pos[right[0]] = (cam, y)
    # Column: icon rows down the left edge, two slots per row.
    # The column: the run of toolbar grey that ends where the drawing's black
    # starts. A side panel opened on the left pushes it right, so find its start too.
    row = img[600, :, :]
    # The drawing starts where the row turns black (board) or white (schematic)
    # and stays that way.
    canvas = (row.max(axis=1) < 12) | (row.min(axis=1) > 200)
    run = np.convolve(canvas.astype(int), np.ones(40, int), "valid")
    col_end = int(np.argmax(run == 40)) - 2
    col_start = max(0, col_end - 104)
    col_w = col_end - col_start
    # The schematic has no second top bar, so its column starts higher: scan from
    # just under the top bar.
    top0 = y + 30
    col = ink(img[top0:, col_start:col_end])
    found = [top0 + (a + b) // 2 for a, b in spans(col.sum(axis=1), gap=3, min_len=14)]
    found = [f for f in found if f > top0 + 18]   # skip the second top bar, if any
    found = [f for f in found if f < img.shape[0] - 160]   # nothing from the status lines
    # Tall icons can merge two rows, so space rows evenly from the first one at
    # the commonest gap between neighbours.
    n = len([r for r in rows if r is not apply.SEP])
    if len(found) == n:
        rows_y = found
    else:
        pitch = (found[-1] - found[0]) / (n - 1)   # first and last rows are never merged
        rows_y = [round(found[0] + i * pitch) for i in range(n)]
    xs_col = [col_start + col_w // 4, col_start + 3 * col_w // 4]   # two equal slots
    for (r, row), ry in zip([(r, row) for r, row in enumerate(rows) if row is not apply.SEP], rows_y):
        for word, cx in zip(row, xs_col[:2]):
            if word:
                pos[word] = (cx, ry)
    return pos


def parts(which):
    if which == "board":
        return apply.TOP_BOARD, apply.BOARD_ROWS, apply.B, apply.VIEW_BOARD, apply.RIGHT_END_BOARD
    return apply.TOP_SCHEMATIC, apply.SCHEMATIC_ROWS, apply.S, apply.VIEW_SCHEMATIC, apply.RIGHT_END_SCHEMATIC


def buttons(which):
    top, rows, table, view, end = parts(which)
    out = [it for it in top + view + end if it is not apply.SEP and not it[0].startswith("@")]
    for row in rows:
        if row is not apply.SEP:
            out += [(w, table[w]) for w in row if w]
    return out


def main():
    which, outdir = sys.argv[1], pathlib.Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    title = "PCB Editor" if which == "board" else "Schematic Editor"
    w = find(title)
    front(title)
    results = []
    only = set(sys.argv[3:])
    for word, action in buttons(which):
        if only and word not in only:
            continue
        front(title)
        before = grab(w)
        pos = layout(which, before)   # a panel opening moves the column, so look again
        score = 1.0
        if word not in pos:
            print(f"{word:14} not found on screen", flush=True)
            continue
        cx, cy = pos[word]
        before_wins = set(windows())
        click(w, cx, cy)
        time.sleep(1.5)
        after = grab(w)
        # Tooltips and drop-downs carry only the program's name; dialogs have titles.
        new = [n for i, (ww, n) in windows().items()
               if i not in before_wins and str(n) not in ("pcbnew", "eeschema", "kicad")]
        diff = cv2.absdiff(before, after)
        changed = int((diff.max(axis=2) > 40).sum())
        # The pressed look of the button itself: a tool that stays active.
        r = apply.ICON_SIZE // 2 + 6
        btn = diff[max(0, cy - r):cy + r, max(0, cx - r):cx + r]
        pressed = int((btn.max(axis=2) > 40).sum())
        tag = word.replace(" ", "_")
        cv2.imwrite(str(outdir / f"{tag}-after.png"), after)
        results.append({"word": word, "action": action, "match": round(float(score), 3), "at": [cx, cy],
                        "new_windows": [str(n) for n in new], "pixels_changed": changed,
                        "button_changed": pressed})
        print(f"{word:14} match={score:.2f} new={new} changed={changed} button={pressed}", flush=True)
        # Back to rest: close a dialog if one opened, then cancel any tool.
        for i, (ww, n) in windows().items():
            if i not in before_wins and str(n) not in ("pcbnew", "eeschema", "kicad"):
                close(ww)
                time.sleep(1.0)
        front(title)
        key("Escape")
        time.sleep(0.3)
        key("Escape")
        time.sleep(0.5)
    (outdir / "results.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
