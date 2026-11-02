#!/usr/bin/env python3
"""Our dark Eagle-style icon set: one SVG per toolbar command, drawn on a
24-unit square, plus the side-by-side sheet against Eagle's own icons.

    python3 icons/make_icons.py [eagle-icon-dir]

Writes icons/svg/<COMMAND>.svg and, when a folder of Eagle's own icons is
given for comparison, icons/sheet.svg. Eagle's pictures are kept as Eagle drew
them in meaning (move is a four-way arrow, delete a cross, route a red track);
only the drawing is ours: thin light strokes, Eagle's layer colours as accents,
no bevelled button.
"""
import base64
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "svg"
SHEET = HERE / "sheet.svg"

FG, DIM = "#d6dbe1", "#7d8590"
RED, GRN, BLU, YEL, CYN = "#ff5a4e", "#3fcf6e", "#4a9eff", "#f2c94c", "#3fd0d0"
W = 1.6  # stroke width on the 24-unit square


def ln(x1, y1, x2, y2, c=FG, w=W, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{w}"{d}/>'


def pth(d, c=FG, w=W, fill="none", dash=None):
    s = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" stroke="{c}" stroke-width="{w}" fill="{fill}"{s}/>'


def cir(x, y, r, c=FG, w=W, fill="none"):
    return f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{c}" stroke-width="{w}" fill="{fill}"/>'


def dot(x, y, r, c):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>'


def box(x, y, w, h, c=FG, sw=W, fill="none", rx=1.5, dash=None):
    s = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" stroke="{c}" stroke-width="{sw}" fill="{fill}"{s}/>'


def txt(x, y, s, size=7, c=FG, weight=600, anchor="middle", family="sans-serif"):
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{c}" text-anchor="{anchor}">{s}</text>')


def arrowhead(x, y, ang, c=FG, s=3):
    import math
    a = math.radians(ang)
    p1 = (x - s * math.cos(a) + s * 0.7 * math.sin(a), y - s * math.sin(a) - s * 0.7 * math.cos(a))
    p2 = (x - s * math.cos(a) - s * 0.7 * math.sin(a), y - s * math.sin(a) + s * 0.7 * math.cos(a))
    return f'<path d="M{p1[0]:.2f} {p1[1]:.2f} L{x} {y} L{p2[0]:.2f} {p2[1]:.2f}" stroke="{c}" stroke-width="{W}" fill="none"/>'


def resistor(y=12, c=FG):
    return ln(3, y, 7, y, c) + box(7, y - 2.5, 10, 5, c, rx=0.5) + ln(17, y, 21, y, c)


def gate(x=5, y=6, c=FG, s=1.0):
    w, h = 9 * s, 12 * s
    return pth(f"M{x} {y} H{x + w * 0.5} A{w * 0.5} {h / 2} 0 0 1 {x + w * 0.5} {y + h} H{x} Z", c)


def magnifier(c=FG):
    return cir(10, 10, 5.5, c) + ln(14, 14, 20, 20, c, 2.4)


DARK = "#16191d"  # the toolbar behind the icons; used to cut shapes out of solid fills


def solid(d, c=FG):
    return f'<path d="{d}" fill="{c}"/>'


def doc(x, y, w=10, h=13, c=FG):
    f = 3
    return pth(f"M{x} {y} H{x + w - f} L{x + w} {y + f} V{y + h} H{x} Z", c, 1.6)


def mag(c=FG):
    return cir(10, 10, 6, c, 2.2) + ln(14.5, 14.5, 20, 20, c, 3)


def chip(x, y, w, h, c=FG):
    legs = "".join(ln(x + 2 + i * (w - 4) / 2, y - 2.5, x + 2 + i * (w - 4) / 2, y, c, 1.4) +
                   ln(x + 2 + i * (w - 4) / 2, y + h, x + 2 + i * (w - 4) / 2, y + h + 2.5, c, 1.4) for i in range(3))
    return box(x, y, w, h, c, 1.6, rx=1) + legs


def trace(c=BLU, end=GRN):
    return pth("M4 6 L10 12 V18 L19 18", c, 2.6) + dot(4, 6, 2.4, end) + dot(19, 18, 2.4, end)


# Eagle 7's flat set, redrawn light on dark: solid shapes, the same colour
# touches Eagle 7 used (blue eye, green route ends, red rip-up cross, green via,
# yellow paste and warning), and Eagle 7's picture for every command.
ICONS = {
    "INFO": cir(12, 12, 9.5, FG, 0, FG) + ln(12, 10.5, 12, 17.5, DARK, 3) + dot(12, 6.8, 1.8, DARK),
    "SHOW": solid("M1.5 12 Q12 2 22.5 12 Q12 22 1.5 12 Z") + cir(12, 12, 4.6, BLU, 0, BLU) + dot(12, 12, 1.8, DARK)
            + dot(10.6, 10.6, 1, "#ffffff"),
    "DISPLAY": box(3, 3, 11, 11, BLU, 0, BLU, rx=1) + box(9, 9, 11, 11, RED, 0, RED, rx=1)
               + solid("M14 18 H22 L18 22 Z", GRN),
    "MARK": ln(4, 21, 21, 21, DIM, 1.4) + ln(4, 4, 4, 21, DIM, 1.4) + ln(14, 7, 14, 17, FG, 2.2) + ln(9, 12, 19, 12, FG, 2.2),
    "MOVE": "".join(solid(d) for d in ("M12 2 L15.5 6.5 H8.5 Z", "M12 22 L15.5 17.5 H8.5 Z",
                                       "M2 12 L6.5 8.5 V15.5 Z", "M22 12 L17.5 8.5 V15.5 Z")) + dot(12, 12, 2, FG),
    "COPY": doc(8, 2) + doc(4, 8, c=FG) + box(5.5, 9.5, 7, 10, FG, 0, FG, rx=0.5),
    "MIRROR": ln(12, 2, 12, 22, DIM, 1.4, "2 1.5") + solid("M3 7 H9 V17 H3 L6 12 Z") + solid("M21 7 H15 V17 H21 L18 12 Z"),
    "ROTATE": cir(12, 12, 8.5, FG, 2) + dot(12, 12, 2.2, FG) + solid("M17 2 L22 6 L16.5 8 Z"),
    "GROUP": box(3.5, 3.5, 17, 17, FG, 0, FG + "cc", rx=1.5) + box(5.5, 5.5, 13, 13, DIM, 0, "#9aa4b1", rx=0.5),
    "CHANGE": solid("M15 2.5 a6 6 0 0 0 -5.6 8.2 L2.8 17.3 a2.6 2.6 0 0 0 3.9 3.9 L13.3 14.6"
                    " a6 6 0 0 0 8.2 -5.6 l-3.6 1.6 -2.7 -2.7 1.6 -3.6 z"),
    "PASTE": dot(9.5, 9.5, 7, YEL) + dot(18.5, 18.5, 3, FG),
    "DELETE": box(5, 7, 14, 15, FG, 0, FG, rx=1.5) + box(3, 4, 18, 2.6, FG, 0, FG, rx=1) + box(9, 1.6, 6, 2.6, FG, 0, FG, rx=1)
              + "".join(ln(x, 10, x, 19, DARK, 1.6) for x in (9, 12, 15)),
    "ADD": gate(3, 4, FG, 0.95) + ln(1, 7, 3, 7) + ln(1, 13, 3, 13) + ln(13, 10, 15, 10)
           + ln(18.5, 13, 18.5, 21, GRN, 2.4) + ln(14.5, 17, 22.5, 17, GRN, 2.4),
    "PINSWAP": solid("M6 3 L9.5 7.5 H2.5 Z") + solid("M6 21 L9.5 16.5 H2.5 Z") + ln(6, 7, 6, 17, FG, 2)
               + pth("M13 5 H20 V19 H13", FG, 2.2),
    "GATESWAP": gate(2, 3, FG, 0.65) + gate(2, 13, FG, 0.65) + pth("M15 6 Q21 12 15 18", CYN, 2) + solid("M15 3.5 L17 7.5 L13 7 Z", CYN)
                + solid("M15 20.5 L17 16.5 L13 17 Z", CYN),
    "REPLACE": box(3, 3, 9, 9, DIM, 0, DIM, rx=1) + box(12, 12, 9, 9, FG, 0, FG, rx=1) + pth("M7 13 V17 H10", GRN, 2)
               + solid("M10 14.5 L13 17 L10 19.5 Z", GRN),
    "LOCK": box(5, 10.5, 14, 11, FG, 0, FG, rx=2) + pth("M8 10.5 V7.5 a4 4 0 0 1 8 0 V10.5", FG, 2.4) + dot(12, 15.5, 1.8, DARK),
    "NAME": txt(12, 10, "R2", 8.5, RED, 800) + ln(4, 13, 20, 13, FG, 1.2) + txt(12, 21.5, "10k", 7.5, DIM, 700),
    "VALUE": txt(12, 10, "R2", 7.5, DIM, 700) + ln(4, 13, 20, 13, FG, 1.2) + txt(11, 21.5, "10k", 8.5, RED, 800),
    "SMASH": chip(3, 9, 10, 8) + txt(18, 8, "&gt;N", 6.5, YEL, 800),
    "MITER": pth("M4 21 V13 Q4 4 13 4 H21", FG, 3.2),
    "SPLIT": pth("M3 20 L10 8 H21", FG, 3) + box(8, 6, 4, 4, YEL, 0, YEL, rx=0.5),
    "OPTIMIZE": ln(3, 9, 21, 9, FG, 2.8) + ln(12, 13, 12, 21, GRN, 2.4) + ln(8, 17, 16, 17, GRN, 2.4),
    "MEANDER": pth("M2 18 V8 a3 3 0 0 1 6 0 V16 a3 3 0 0 0 6 0 V8 a3 3 0 0 1 6 0 V18", FG, 2.4),
    "ROUTE": trace(),
    "RIPUP": trace(DIM) + ln(12, 9, 17, 14, RED, 2.6) + ln(17, 9, 12, 14, RED, 2.6),
    "WIRE": box(3, 3, 18, 18, DIM, 1.4, "#2a2f36", rx=2) + ln(7, 17, 17, 7, FG, 3),
    "TEXT": txt(12, 20, "T", 20, FG, 800, family="sans-serif"),
    "CIRCLE": cir(12, 12, 8.5, FG, 2.8),
    "ARC": pth("M3 16 A10 10 0 0 1 21 16", FG, 2.8),
    "RECT": box(4, 4, 16, 16, FG, 0, FG, rx=0.5),
    "POLYGON": solid("M4 20 V10 L12 4 H20 V20 Z", FG + "00") + pth("M4 20 V11 L11 4 H20 V20 Z", FG, 2.4),
    "VIA": "".join(f'<ellipse cx="12" cy="{y}" rx="8.5" ry="3.2" fill="{GRN}" stroke="{DARK}" stroke-width="1"/>' for y in (17, 12, 7))
           + f'<ellipse cx="12" cy="7" rx="3" ry="1.1" fill="{DARK}"/>',
    "SIGNAL": ln(5, 12, 19, 12, YEL, 2.4) + dot(5, 12, 3, GRN) + dot(19, 12, 3, GRN),
    "HOLE": "".join(f'<ellipse cx="12" cy="{y}" rx="8.5" ry="3.2" fill="{DIM}" stroke="{DARK}" stroke-width="1"/>' for y in (15, 9))
            + f'<ellipse cx="12" cy="9" rx="3" ry="1.1" fill="{DARK}"/>',
    "ATTRIBUTE": gate(3, 4, FG, 0.95) + txt(9, 13.5, "AT", 6.5, FG, 800),
    "DIMENSION": ln(3, 7, 3, 17, FG, 1.8) + ln(21, 7, 21, 17, FG, 1.8) + ln(5, 12, 19, 12, FG, 1.8)
                 + solid("M4.5 12 L8 9.8 V14.2 Z") + solid("M19.5 12 L16 9.8 V14.2 Z"),
    "RATSNEST": "".join(ln(12, 12, x, y, FG, 1.2) for x, y in ((4, 5), (20, 5), (4, 19), (20, 19), (12, 3)))
                + "".join(dot(x, y, 2.2, FG) for x, y in ((4, 5), (20, 5), (4, 19), (20, 19), (12, 3))) + dot(12, 12, 3, FG),
    "AUTO": txt(6, 21, "A", 10, FG, 800) + pth("M9 4 L14 9 V14 L21 14", BLU, 2.4) + dot(9, 4, 2.2, GRN) + dot(21, 14, 2.2, GRN),
    "DRC": box(2, 3, 15, 13, FG, 0, DIM, rx=1) + ln(5, 7, 13, 7, FG, 1.4) + ln(9, 7, 9, 13, FG, 1.4)
           + cir(17, 17, 5.5, GRN, 0, GRN) + pth("M14.5 17 L16.5 19 L19.8 15", DARK, 1.8),
    "ERC": gate(2, 3, FG, 0.75) + cir(17, 17, 5.5, GRN, 0, GRN) + pth("M14.5 17 L16.5 19 L19.8 15", DARK, 1.8),
    "ERRORS": solid("M12 2 L23 21 H1 Z", YEL) + ln(12, 9, 12, 15, DARK, 2.4) + dot(12, 18, 1.4, DARK),
    "BUS": ln(3, 7, 21, 7, BLU, 3.4) + ln(8, 7, 12, 12, BLU, 1.6) + ln(12, 12, 12, 21, GRN, 2)
           + ln(15, 7, 19, 12, BLU, 1.6) + ln(19, 12, 19, 21, GRN, 2),
    "NET": ln(3, 12, 21, 12, GRN, 2.8) + dot(3, 12, 2.4, GRN) + dot(21, 12, 2.4, GRN),
    "JUNCTION": ln(2, 12, 22, 12, GRN, 2.2) + ln(12, 12, 12, 22, GRN, 2.2) + dot(12, 12, 4, GRN),
    "LABEL": ln(2, 18, 11, 18, GRN, 2.2) + txt(15, 13, "ABC", 7, FG, 800),
    "SUPPLY": ln(12, 22, 12, 10, GRN, 2.2) + box(5, 7.5, 14, 3, RED, 0, RED, rx=0.5) + txt(12, 6, "+5V", 6, RED, 800),
    "NO CONNECT": ln(2, 12, 12, 12, GRN, 2.2) + ln(8.5, 6.5, 17.5, 15.5, BLU, 2.6) + ln(17.5, 6.5, 8.5, 15.5, BLU, 2.6),
    "PORT": ln(1, 12, 6, 12, GRN, 2.2) + solid("M6 6.5 H16 L22 12 L16 17.5 H6 Z"),
    "ANNOTATE": txt(7, 10, "U?", 7.5, DIM, 800) + ln(9, 14, 15, 14, CYN, 2) + solid("M15 11.5 L18.5 14 L15 16.5 Z", CYN)
                + txt(17, 22, "U1", 7.5, FG, 800),
    "GRID": "".join(box(x, y, 4, 4, FG, 0, FG, rx=0.4) for x in (4, 10, 16) for y in (4, 10, 16)),
    "UNITS": box(2, 7, 20, 10, FG, 0, FG, rx=1.5) + "".join(ln(x, 7, x, 10.5 if i % 2 else 12.5, DARK, 1.2) for i, x in enumerate(range(5, 21, 3))),
    "HIDDEN PINS": box(10, 3, 11, 18, FG, 0, FG, rx=1) + ln(2, 7, 10, 7, GRN, 2) + ln(2, 17, 10, 17, GRN, 2, "1.5 1.5"),
    "AIRWIRES": ln(5, 19, 19, 5, YEL, 1.4) + dot(5, 19, 3, GRN) + dot(19, 5, 3, GRN),
    # Top bar
    "OPEN": doc(4, 2, 12, 17) + pth("M10 13 H21", BLU, 2.4) + solid("M18 9.5 L22.5 13 L18 16.5 Z", BLU),
    "SAVE": solid("M3 3 H17 L21 7 V21 H3 Z") + box(7, 3, 9, 6, DARK, 0, DARK, rx=0.5) + box(6, 13, 12, 8, DARK, 0, DARK, rx=0.5)
            + box(12, 4, 2.5, 4, FG, 0, FG, rx=0.3),
    "PRINT": box(6, 2, 12, 6, FG, 0, FG, rx=0.5) + box(2, 8, 20, 9, FG, 0, FG, rx=1.5) + box(6, 14, 12, 8, FG, 1.4, DARK, rx=0.5)
             + dot(18.5, 11, 1.2, GRN),
    "CAM": box(2, 6, 20, 14, FG, 0, FG, rx=2.5) + box(7, 3, 6, 4, FG, 0, FG, rx=1) + cir(12, 13, 5, DARK, 0, DARK)
           + cir(12, 13, 3.6, BLU, 0, BLU),
    "BOARD": gate(1.5, 3, FG, 0.62) + chip(13, 13, 8, 7, RED) + pth("M8 8 V16 H11", CYN, 2) + solid("M11 13.5 L14 16 L11 18.5 Z", CYN),
    "SCHEMATIC": chip(2, 4, 8, 7, RED) + gate(14.5, 13, FG, 0.62) + pth("M6 13 V17 H11", CYN, 2) + solid("M11 14.5 L14 17 L11 19.5 Z", CYN),
    "USE": "".join(box(x, 3, 4.5, 18, FG, 0, FG, rx=1) + box(x + 1.2, 6, 2.1, 4, DARK, 0, DARK, rx=0.4) for x in (3, 9.75, 16.5)),
    "RUN": box(2, 3, 20, 18, FG, 0, FG, rx=2) + pth("M6 9 L10 12.5 L6 16", DARK, 2.2) + ln(12, 16, 18, 16, DARK, 2.2),
    "FIT": mag() + box(7, 7, 6, 6, FG, 0, FG, rx=0.5),
    "ZOOM IN": mag() + ln(10, 6.8, 10, 13.2, FG, 2.2) + ln(6.8, 10, 13.2, 10, FG, 2.2),
    "ZOOM OUT": mag() + ln(6.8, 10, 13.2, 10, FG, 2.2),
    "REDRAW": mag() + dot(10, 10, 2.2, FG),
    "ZOOM SELECT": mag() + box(6.8, 6.8, 6.4, 6.4, FG, 1.2, rx=0.4, dash="1.5 1") + solid("M17 17 H23 L20 21 Z"),
    "UNDO": solid("M3 9 L9 4 V7 H14 a6 6 0 0 1 0 12 H9 V15.5 H14 a2.5 2.5 0 0 0 0 -5 H9 V14 Z"),
    "REDO": solid("M21 9 L15 4 V7 H10 a6 6 0 0 0 0 12 H15 V15.5 H10 a2.5 2.5 0 0 1 0 -5 H15 V14 Z"),
    "FIND": mag() + txt(10, 13.5, "?", 9, YEL, 800),
    "UPDATE BOARD": gate(1.5, 3, FG, 0.62) + chip(13, 13, 8, 7, RED) + pth("M9 15 A6 6 0 0 1 16 8", CYN, 2)
                    + solid("M14 6 L18.5 7.5 L15.5 11 Z", CYN),
}

ORDER = {
    "Top bar, schematic": ["OPEN", "SAVE", "PRINT", "CAM", "BOARD", "USE", "FIT", "ZOOM IN", "ZOOM OUT", "REDRAW",
                           "ZOOM SELECT", "UNDO", "REDO", "FIND"],
    "Top bar, board": ["OPEN", "SAVE", "PRINT", "CAM", "SCHEMATIC", "USE", "RUN", "FIT", "ZOOM IN", "ZOOM OUT",
                       "REDRAW", "ZOOM SELECT", "UNDO", "REDO", "FIND", "UPDATE BOARD"],
    "Left column, schematic": ["INFO", "SHOW", "MARK", "MOVE", "COPY", "MIRROR", "ROTATE", "GROUP", "CHANGE", "PASTE", "DELETE",
                  "ADD", "PINSWAP", "REPLACE", "NAME", "VALUE", "SPLIT", "WIRE", "TEXT", "CIRCLE", "ARC", "RECT",
                  "BUS", "NET", "JUNCTION", "LABEL", "SUPPLY", "NO CONNECT", "PORT", "ATTRIBUTE", "ANNOTATE", "ERC"],
    "Left column, board": ["INFO", "SHOW", "DISPLAY", "MARK", "MOVE", "COPY", "MIRROR", "ROTATE", "GROUP", "CHANGE", "PASTE",
              "DELETE", "ADD", "PINSWAP", "GATESWAP", "REPLACE", "LOCK", "MITER", "SPLIT", "OPTIMIZE", "ROUTE",
              "RIPUP", "WIRE", "TEXT", "CIRCLE", "ARC", "RECT", "POLYGON", "VIA", "DIMENSION", "RATSNEST", "AUTO", "DRC"],
    "Right side, both": ["GRID", "UNITS", "HIDDEN PINS", "AIRWIRES"],
}


def icon_svg(body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="100%" height="100%" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


def sheet(eagle_dir):
    cols, cell, gap = 5, 150, 14
    rows = []
    for section, names in ORDER.items():
        rows.append(("H", section))
        for i in range(0, len(names), cols):
            rows.append(("R", names[i:i + cols]))
    y, parts = 70, []
    for kind, val in rows:
        if kind == "H":
            parts.append(txt(24, y + 26, val, 20, "#e8ecf0", 700, "start"))
            y += 44
            continue
        for j, name in enumerate(val):
            x = 24 + j * (cell * 2 + gap)
            parts.append(f'<rect x="{x}" y="{y}" width="{cell * 2}" height="{cell - 22}" rx="10" fill="#22272e"/>')
            parts.append(txt(x + cell, y + cell - 38, name, 14, "#e8ecf0", 700))
            # Eagle used one button for both directions between schematic and board.
            png = eagle_dir / f"{ {'SCHEMATIC': 'BOARD'}.get(name, name)}.png" if eagle_dir else None
            if png and png.exists():
                b64 = base64.b64encode(png.read_bytes()).decode()
                parts.append(f'<rect x="{x + 22}" y="{y + 12}" width="64" height="64" rx="6" fill="#e6e6e6"/>')
                parts.append(f'<image x="{x + 26}" y="{y + 16}" width="56" height="56" href="data:image/png;base64,{b64}" xlink:href="data:image/png;base64,{b64}"/>')
            else:
                parts.append(txt(x + 54, y + 50, "none", 11, DIM, 400))
            parts.append(f'<rect x="{x + cell + 8}" y="{y + 12}" width="64" height="64" rx="6" fill="#16191d"/>')
            # Groups, not nested pictures: some viewers draw a nested picture as an empty box.
            parts.append(f'<g transform="translate({x + cell + 12} {y + 16}) scale({56 / 24})" '
                         f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')
            parts.append(f'<g transform="translate({x + cell + 88} {y + 32})" '
                         f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')
        y += cell - 8
    width = 24 * 2 + cols * (cell * 2 + gap) - gap
    head = txt(24, 40, "Eagle 7's command icons, and our dark versions", 24, "#ffffff", 700, "start")
    note = txt(width - 24, 40, "In each box: Eagle 7 on the left (cut from its manual's screenshot), ours on the right, then ours at real size", 13, DIM, 400, "end")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {width} {y + 30}" width="100%" height="100%" '
            f'preserveAspectRatio="xMidYMin meet"><rect width="100%" height="100%" fill="#0f1215"/>'
            f'{head}{note}{"".join(parts)}</svg>')


def main():
    OUT.mkdir(exist_ok=True)
    for name, body in ICONS.items():
        (OUT / f"{name.replace(' ', '_')}.svg").write_text(icon_svg(body))
    print(f"{len(ICONS)} icons in {OUT}")
    if len(sys.argv) > 1:
        SHEET.parent.mkdir(parents=True, exist_ok=True)
        SHEET.write_text(sheet(pathlib.Path(sys.argv[1])))
        print("sheet", SHEET)


if __name__ == "__main__":
    main()
