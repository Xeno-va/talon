#!/usr/bin/env python3
"""Test Eagle's command-then-click: click a command, click a part, see it act.

    python3 test/verbs.py board|schematic <x> <y> <out-dir> WORD...

<x> <y> is a point on a part, in the editor window. For each command: click the
button, click the part, record what changed and any window that opened, close
that window, press Escape twice, undo with F9, and check the drawing came back.
"""
import json
import pathlib
import sys
import time

import cv2

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import drive  # noqa: E402


def main():
    which, tx, ty, outdir = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), pathlib.Path(sys.argv[4])
    words = sys.argv[5:]
    outdir.mkdir(parents=True, exist_ok=True)
    title = "PCB Editor" if which == "board" else "Schematic Editor"
    w = drive.find(title)
    results = []
    for word in words:
        drive.front(title)
        base = drive.grab(w)
        pos = drive.layout(which, base)
        before_wins = set(drive.windows())
        drive.click(w, *pos[word])
        time.sleep(0.8)
        drive.click(w, tx, ty)
        time.sleep(1.5)
        after = drive.grab(w)
        new = [(i, ww, n) for i, (ww, n) in drive.windows().items()
               if i not in before_wins and str(n) not in ("pcbnew", "eeschema", "kicad")]
        # Only the drawing counts; the toolbar and status lines change on any click.
        d = cv2.absdiff(base, after).max(axis=2) > 40
        changed = int(d[150:-120, 130:].sum())
        cv2.imwrite(str(outdir / f"{word.replace(' ', '_')}-before.png"), base)
        cv2.imwrite(str(outdir / f"{word.replace(' ', '_')}.png"), after)
        for _, ww, _ in new:
            drive.close(ww)
            time.sleep(1.0)
        drive.front(title)
        drive.key("Escape")
        time.sleep(0.3)
        drive.key("Escape")
        time.sleep(0.4)
        time.sleep(0.6)
        # What is still different once the selection is gone is what the command did.
        def near(img):
            return img[max(0, ty - 150):ty + 150, max(0, tx - 150):tx + 150]
        kept = int((cv2.absdiff(near(base), near(drive.grab(w))).max(axis=2) > 40).sum())
        drive.key("F9")
        time.sleep(1.2)
        restored = int((cv2.absdiff(near(base), near(drive.grab(w))).max(axis=2) > 40).sum())
        r = {"word": word, "changed": changed, "kept": kept, "dialogs": [str(n) for _, _, n in new],
             "left_over": restored}
        results.append(r)
        print(f"{word:12} kept_after_escape={kept:6} dialogs={r['dialogs']} after_undo={restored}", flush=True)
    (outdir / "results.json").write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    main()
