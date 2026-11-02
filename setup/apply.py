#!/usr/bin/env python3
"""Make KiCad 10 look and work like Eagle 7, through KiCad's own settings only.

    python3 setup/apply.py            write it (KiCad must be closed)
    python3 setup/apply.py --check    say what would be written, write nothing

Writes, in ~/.config/kicad/10.0/:
  toolbars/eeschema-toolbars.json, toolbars/pcbnew-toolbars.json
      Eagle's action bar across the top, its command column down the left,
      KiCad's view switches on the right.
  user.hotkeys
      Eagle's key table; KiCad defaults that collide with it moved off.
  ~/.local/share/kicad-eagle/
      KiCad's own data folder, linked, with our icons swapped into its icon
      pack. KiCad is pointed at it by ~/.config/environment.d/kicad-eagle.conf
      (from the next login) and by the launch line printed at the end.
  ~/.local/share/kicad/10.0/template/default/default.kicad_pcb
      An empty two-layer board with Eagle's layer names, copied into every
      new project KiCad makes.
  colors/eagle7.json
      Our Eagle-style colours, started from the CC0 "eagle-dark" scheme.
  eeschema.json, pcbnew.json
      Custom toolbars switched on and the colours selected.

Run it again after every KiCad upgrade. Every action name is checked against
the list read out of the installed KiCad; a name KiCad no longer has is
reported and left off, never written.

KiCad rewrites its settings on exit, so writing while it is open is lost.
"""
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CFG = pathlib.Path.home() / ".config/kicad/10.0"
CHECK = "--check" in sys.argv

KNOWN = set()
for f in (HERE / "kicad-actions").glob("*.txt"):
    KNOWN |= set(f.read_text().split())

SEP = None

# Eagle 7's command column is two icons wide. Each row is (outer, inner); None is
# an empty cell, SEP a gap across both. The board rows follow the board editor
# screenshot in Eagle 7's manual exactly; the schematic rows keep the same
# pairings where both editors share a command. Eagle commands KiCad has no
# counterpart for are left out, and so are the ones KiCad gives no picture
# (miter, auto), which would show as blank buttons.
# INFO opens the clicked item's properties, as Eagle's did. On the board CHANGE
# opens track and via sizes, the nearest KiCad has to Eagle's change menu. DELETE is the plain delete, which the patched toolbar runs on each
# item clicked.
T = {
    "MARK": "common.Interactive.measureTool",
    "COPY": "common.Interactive.duplicate", "GROUP": "common.Interactive.selectSetRect",
    "PASTE": "common.Interactive.paste", "DELETE": "common.Interactive.delete",
}
S = dict(T, **{
    "SHOW": "eeschema.EditorControl.highlightNetTool",
    "MOVE": "eeschema.InteractiveMove.move", "MIRROR": "eeschema.InteractiveEdit.mirrorV",
    "ROTATE": "eeschema.InteractiveEdit.rotateCCW",
    "INFO": "eeschema.InteractiveEdit.properties",
    "ADD": "eeschema.InteractiveDrawing.placeSymbol", "PINSWAP": "eeschema.InteractiveEdit.swapPins",
    "REPLACE": "eeschema.InteractiveEdit.changeSymbol", "NAME": "eeschema.InteractiveEdit.editReference",
    "VALUE": "eeschema.InteractiveEdit.editValue", "SPLIT": "eeschema.InteractiveEdit.breakWire",
    "WIRE": "eeschema.InteractiveDrawingLineWireBus.drawLines",
    "TEXT": "eeschema.InteractiveDrawing.placeSchematicText", "CIRCLE": "eeschema.InteractiveDrawing.drawCircle",
    "ARC": "eeschema.InteractiveDrawing.drawArc", "RECT": "eeschema.InteractiveDrawing.drawRectangle",
    "BUS": "eeschema.InteractiveDrawingLineWireBus.drawBuses",
    "NET": "eeschema.InteractiveDrawingLineWireBus.drawWires",
    "JUNCTION": "eeschema.InteractiveDrawing.placeJunction", "LABEL": "eeschema.InteractiveDrawing.placeLabel",
    "SUPPLY": "eeschema.InteractiveDrawing.placePowerSymbol",
    "NO CONNECT": "eeschema.InteractiveDrawing.placeNoConnect",
    "PORT": "eeschema.InteractiveDrawing.placeHierarchicalLabel",
    "ATTRIBUTE": "eeschema.EditorControl.editSymbolFields", "ANNOTATE": "eeschema.EditorControl.annotate",
    "ERC": "eeschema.InspectionTool.runERC",
})
B = dict(T, **{
    # KiCad's board editor has no click-on-a-net tool: select a pad or track,
    # then SHOW highlights its whole net. The ` key highlights the net under the cursor.
    "SHOW": "pcbnew.EditorControl.highlightNetSelection", "DISPLAY": "pcbnew.Control.showLayersManager",
    "MOVE": "pcbnew.InteractiveMove.move", "MIRROR": "pcbnew.InteractiveEdit.flip",
    "ROTATE": "pcbnew.InteractiveEdit.rotateCcw", "CHANGE": "pcbnew.GlobalEdit.editTracksAndVias",
    "INFO": "pcbnew.InteractiveEdit.properties",
    "ADD": "pcbnew.EditorControl.placeFootprint", "PINSWAP": "pcbnew.InteractiveEdit.swapPadNets",
    "GATESWAP": "pcbnew.InteractiveEdit.swapGateNets", "REPLACE": "pcbnew.GlobalEdit.changeFootprint",
    "LOCK": "pcbnew.EditorControl.toggleLock", "SPLIT": "pcbnew.InteractiveRouter.BreakTrack",
    "OPTIMIZE": "pcbnew.GlobalEdit.cleanupTracksAndVias", "ROUTE": "pcbnew.InteractiveRouter.SingleTrack",
    "RIPUP": "pcbnew.InteractiveSelection.unrouteSelected", "WIRE": "pcbnew.InteractiveDrawing.line",
    "TEXT": "pcbnew.InteractiveDrawing.text", "CIRCLE": "pcbnew.InteractiveDrawing.circle",
    "ARC": "pcbnew.InteractiveDrawing.arc", "RECT": "pcbnew.InteractiveDrawing.rectangle",
    "POLYGON": "pcbnew.InteractiveDrawing.zone", "VIA": "pcbnew.InteractiveDrawing.via",
    "DIMENSION": "pcbnew.InteractiveDrawing.alignedDimension", "RATSNEST": "pcbnew.ZoneFiller.zoneFillAll",
    "DRC": "pcbnew.DRCTool.runDRC",
})
# Eagle 7's pairs, with its single-tool rows doubled up and no gaps between
# groups, so the whole column fits a 1200-pixel-high window at 40-pixel icons.
SCHEMATIC_ROWS = [
    # A blank cell in a vertical bar takes no space in KiCad, so it would slide
    # the rest of that column up a row; the only blank is the last cell.
    # No CHANGE here: KiCad's only counterpart works in the symbol editor, and INFO
    # already opens the clicked symbol's properties.
    ("INFO", "SHOW"), ("MOVE", "COPY"), ("MIRROR", "ROTATE"), ("GROUP", "RECT"), ("PASTE", "DELETE"),
    ("ADD", "PINSWAP"), ("REPLACE", "SPLIT"), ("NAME", "VALUE"), ("WIRE", "TEXT"), ("CIRCLE", "ARC"),
    ("BUS", "NET"), ("JUNCTION", "LABEL"), ("SUPPLY", "NO CONNECT"), ("PORT", "ERC"),
    ("ATTRIBUTE", "ANNOTATE"),
]
BOARD_ROWS = [
    ("INFO", "SHOW"), ("DISPLAY", "MARK"), ("MOVE", "COPY"), ("MIRROR", "ROTATE"), ("GROUP", "CHANGE"),
    ("PASTE", "LOCK"), ("DELETE", "ADD"), ("PINSWAP", "REPLACE"), ("GATESWAP", "OPTIMIZE"), ("SPLIT", "RIPUP"),
    ("ROUTE", "VIA"), ("WIRE", "TEXT"), ("CIRCLE", "ARC"), ("RECT", "POLYGON"), ("DIMENSION", "RATSNEST"),
    ("DRC", None),
]


def split_rows(rows, table):
    """The two columns, cell by cell: a blank cell is a gap one button high."""
    outer, inner = [], []
    for row in rows:
        if row is SEP:
            outer.append(SEP)
            inner.append(SEP)
            continue
        for word, col in zip(row, (outer, inner)):
            col.append((word, table[word]) if word else ("@spacer", ICON_SIZE + 8))
    return outer, inner


# Eagle's action bar across the top, in Eagle's order. KiCad's second top row on
# the board (track width, via size, layer, grid, zoom) is its version of Eagle's
# parameter bar and is left as KiCad draws it.
TOP_SCHEMATIC = [
    ("OPEN", "common.Control.open"), ("SAVE", "common.Control.save"), ("PRINT", "common.Control.print"),
    ("USE", "common.Control.showSymbolEditor"),
    SEP,
    ("FIT", "common.Control.zoomFitScreen"), ("ZOOM IN", "common.Control.zoomInCenter"),
    ("ZOOM OUT", "common.Control.zoomOutCenter"), ("REDRAW", "common.Control.zoomRedraw"),
    ("ZOOM SELECT", "common.Control.zoomTool"),
    SEP,
    ("UNDO", "common.Interactive.undo"), ("REDO", "common.Interactive.redo"),
    SEP,
    ("FIND", "common.Interactive.find"),
]
TOP_BOARD = [
    ("OPEN", "common.Control.open"), ("SAVE", "common.Control.save"), ("PRINT", "common.Control.print"),
    ("USE", "common.Control.showFootprintEditor"),
    SEP,
    ("FIT", "common.Control.zoomFitScreen"), ("ZOOM IN", "common.Control.zoomInCenter"),
    ("ZOOM OUT", "common.Control.zoomOutCenter"), ("REDRAW", "common.Control.zoomRedraw"),
    ("ZOOM SELECT", "common.Control.zoomTool"),
    SEP,
    ("UNDO", "common.Interactive.undo"), ("REDO", "common.Interactive.redo"),
    SEP,
    ("FIND", "common.Interactive.find"), ("UPDATE BOARD", "common.Control.updatePcbFromSchematic"),
]

# The owner's order for the right-hand end of the top bar, in both editors:
# CAM output, then (board only) Push to SolidCraft, then the switch between
# schematic and board at the far right. The spacer pushes them there; its width
# is for a maximised 1920-pixel window until the patched KiCad can stretch it.
# The patched KiCad, once built and installed, beside the official one.
PATCHED = pathlib.Path.home() / ".local/opt/kicad-eagle/bin"
HAVE_PATCHED = (PATCHED / "kicad").exists()
# The patched KiCad stretches a gap of -1 to push what follows to the far end.
SPACER_SCHEMATIC = -1 if HAVE_PATCHED else 900
SPACER_BOARD = -1 if HAVE_PATCHED else 620
RIGHT_END_SCHEMATIC = [("@spacer", SPACER_SCHEMATIC), ("CAM", "common.Control.plot"),
                       ("BOARD", "eeschema.EditorControl.showPcbNew")]
# KiCad's plugin-button area holds its scripting console and every plugin
# button, Push to SolidCraft among them; it cannot be split.
RIGHT_END_BOARD = [("@spacer", SPACER_BOARD), ("CAM", "common.Control.plot"),
                   ("@control", "control.IPCPlugin"),
                   ("SCHEMATIC", "pcbnew.EditorControl.showEeschema")]
ICON_SIZE = 40  # KiCad's default is 24; the owner could not see them

VIEW_SCHEMATIC = [("GRID", "common.Control.toggleGrid"), ("UNITS", "common.Control.toggleUnits"),
                  SEP, ("HIDDEN PINS", "eeschema.EditorControl.showHiddenPins")]
VIEW_BOARD = [("GRID", "common.Control.toggleGrid"), ("UNITS", "common.Control.toggleUnits"),
              SEP, ("AIRWIRES", "pcbnew.Control.showRatsnest")]

# Eagle's default key table, read off the key-assignment window pictured in its
# version 6 manual, plus F9/F10 from the same manual and Alt+F7 measure (the
# owner's habit). Each key
# goes to the KiCad action that does the same job; an Eagle command KiCad has no
# counterpart for (GROUP as a box, ERRORS, HOLE, SIGNAL, SMASH) is left out.
EAGLE_KEYS = [
    ("Alt+F2", ["common.Control.zoomFitScreen"]),
    ("F2", ["common.Control.zoomRedraw"]),
    ("F3", ["common.Control.zoomIn"]),
    ("F4", ["common.Control.zoomOut"]),
    ("F5", ["common.Control.zoomCenter"]),
    ("F6", ["common.Control.toggleGrid"]),
    # KiCad takes two keys per command. Undo and redo keep the everyday Ctrl+Z
    # and Ctrl+Y first, with Eagle's F9 and F10 second.
    ("Ctrl+Z", ["common.Interactive.undo"]),
    ("F9", ["common.Interactive.undo"]),
    ("Ctrl+Y", ["common.Interactive.redo"]),
    ("F10", ["common.Interactive.redo"]),
    ("Alt+F7", ["common.Interactive.measureTool"]),
    ("Ctrl+Shift+A", ["eeschema.InteractiveDrawing.placeSymbol", "pcbnew.EditorControl.placeFootprint"]),
    ("Ctrl+Shift+C", ["common.Interactive.duplicate"]),
    ("Ctrl+D", ["common.Interactive.deleteTool"]),
    ("Ctrl+Shift+D", ["pcbnew.DRCTool.runDRC", "eeschema.InspectionTool.runERC"]),
    ("Ctrl+F", ["common.Interactive.find"]),
    ("Ctrl+I", ["common.Control.showProperties"]),
    ("Ctrl+M", ["eeschema.InteractiveMove.move", "pcbnew.InteractiveMove.move"]),
    ("Ctrl+Shift+N", ["eeschema.InteractiveEdit.editReference"]),
    ("Ctrl+Shift+P", ["pcbnew.InteractiveDrawing.zone"]),
    ("Ctrl+R", ["pcbnew.InteractiveRouter.SingleTrack"]),
    ("Ctrl+Shift+R", ["pcbnew.InteractiveSelection.unrouteSelected"]),
    ("Ctrl+T", ["eeschema.InteractiveDrawing.placeSchematicText", "pcbnew.InteractiveDrawing.text"]),
    ("Ctrl+Shift+V", ["eeschema.InteractiveEdit.editValue"]),
    ("Ctrl+W", ["eeschema.InteractiveDrawingLineWireBus.drawLines", "pcbnew.InteractiveDrawing.line"]),
]

# Eagle's mouse, from the same manual: the wheel zooms, holding the wheel or
# middle button and moving pans, the right button does nothing when dragged.
# Zooming keeps the point under the cursor still rather than re-centring
# (UNVERIFIED). Values are KiCad's: 2 = pan, 3 = nothing.
MOUSE = {
    "mouse_middle": 2,
    "mouse_right": 3,
    "scroll_modifier_zoom": 0,
    "center_on_zoom": False,
}


def scope(action):
    return action.split(".")[0]


def clash(a, b):
    return scope(a) == scope(b) or "common" in (scope(a), scope(b))


def build_hotkeys():
    """Eagle keys first, KiCad's default kept as a second key where it is free,
    and every KiCad default that an Eagle key would collide with taken off."""
    defaults = {}
    for f in (HERE / "kicad-actions").glob("default-hotkeys-*.json"):
        defaults.update(json.loads(f.read_text()))
    keys = {}
    for key, actions in EAGLE_KEYS:
        for a in actions:
            if a not in KNOWN:
                problems.append(f"key {key}: KiCad has no action {a}; left off")
                continue
            keys.setdefault(a, []).append(key)
    taken = [(k, a) for a, ks in keys.items() for k in ks]

    def free(key, action):
        return not any(k == key and clash(a, action) for k, a in taken)

    def unclaimed(key, action):
        # A KiCad default kept as a second key must not push another tool off its own.
        return not any(key in ds and o != action and clash(o, action)
                       for o, ds in defaults.items() if o not in keys)

    for a, ks in keys.items():
        for d in defaults.get(a, []):
            if d and len(ks) < 2 and d not in ks and free(d, a) and unclaimed(d, a):
                ks.append(d)
                taken.append((d, a))
    for a, (d1, d2) in defaults.items():
        if a in keys or a not in KNOWN:
            continue
        kept = [d for d in (d1, d2) if d and free(d, a)]
        if kept != [d for d in (d1, d2) if d]:
            keys[a] = kept or ["<unassigned>"]
    return keys

# Eagle 7's palette as we remember it: black board, red top copper, blue bottom,
# green pads and vias, yellow airwires, light grey silkscreen. UNVERIFIED against
# a running Eagle 7; adjust here and re-run.
BOARD_COLOURS = {
    "background": "rgb(0, 0, 0)",
    "grid": "rgb(80, 80, 80)",
    "copper": {"f": "rgba(204, 0, 0, 0.800)", "b": "rgba(0, 0, 204, 0.800)"},
    "pad_through_hole": "rgb(0, 170, 0)",
    "plated_hole": "rgb(0, 120, 0)",
    "via_through": "rgb(0, 170, 0)",
    "ratsnest": "rgb(200, 200, 0)",
    "f_silks": "rgb(200, 200, 200)",
    "b_silks": "rgb(140, 140, 200)",
    "edge_cuts": "rgb(220, 220, 220)",
}
SCHEMATIC_COLOURS = {
    "background": "rgb(255, 255, 255)",
    "grid": "rgb(200, 200, 200)",
    "wire": "rgb(0, 140, 0)",
    "junction": "rgb(0, 140, 0)",
    "bus": "rgb(0, 0, 200)",
    "bus_junction": "rgb(0, 0, 200)",
    "component_outline": "rgb(160, 0, 0)",
    "component_body": "rgb(255, 255, 255)",
    "pin": "rgb(0, 140, 0)",
    "pin_name": "rgb(100, 100, 100)",
    "pin_number": "rgb(100, 100, 100)",
    "reference": "rgb(80, 80, 80)",
    "value": "rgb(80, 80, 80)",
    "fields": "rgb(80, 80, 80)",
    "label_local": "rgb(0, 0, 0)",
    "label_global": "rgb(0, 0, 0)",
    "label_hier": "rgb(0, 0, 0)",
    "note": "rgb(0, 0, 160)",
    "sheet": "rgb(160, 0, 0)",
    "cursor": "rgb(0, 0, 0)",
}

# Eagle has no side panels: the drawing runs from the command column to the
# window's edge. KiCad's panels start hidden; DISPLAY still opens the layers.
PANELS = {
    "eeschema": {"show_properties": False, "show_schematic_hierarchy": False, "show_search": False,
                 "show_net_nav_panel": False, "design_blocks_show": False},
    "pcbnew": {"show_layer_manager": False, "show_properties": False, "show_search": False,
               "show_net_inspector": False, "design_blocks_show": False},
}

# Where two of our commands share one KiCad picture, the one listed wins.
SHARED_PICTURE = {"swap": "PINSWAP", "erc": "DRC"}
STOCK = pathlib.Path("/usr/share/kicad")
SKIN_DATA = pathlib.Path.home() / ".local/share/kicad-eagle"
ENVFILE = pathlib.Path.home() / ".config/environment.d/kicad-eagle.conf"
SIZES = (16, 24, 32, 48, 64)

problems = []


def column(items):
    out = []
    for it in items:
        if it is SEP:
            if out and out[-1]["type"] != "SEPARATOR":
                out.append({"type": "SEPARATOR"})
            continue
        word, name = it
        if word == "@spacer":
            out.append({"type": "SPACER", "size": name})
            continue
        if word == "@control":
            out.append({"type": "CONTROL", "name": name})
            continue
        if name not in KNOWN:
            problems.append(f"{word}: KiCad has no action {name}; left off")
            continue
        out.append({"type": "TOOL", "name": name})
    return out


def toolbars(top, rows, table, view, end):
    # The view switches join the top bar, where Eagle keeps its grid button. The
    # two halves of the command column go in KiCad's left and right toolbars; the
    # patched KiCad docks the right one beside the left.
    outer, inner = split_rows(rows, table)
    return {"meta": {"version": 1},
            "toolbars": [{"name": "TOP_MAIN", "contents": column(top + [SEP] + view + end)},
                         {"name": "LEFT", "contents": column(outer)},
                         {"name": "RIGHT", "contents": column(inner)}]}


def merge(base, over):
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            merge(base[k], v)
        else:
            base[k] = v
    return base


def pictures():
    """KiCad picture name -> our command word, for every button we place."""
    icon_of = {}
    for f in (HERE / "kicad-actions").glob("action-icons-*.json"):
        icon_of.update(json.loads(f.read_text()))
    out = {}
    for items in (TOP_SCHEMATIC, *split_rows(SCHEMATIC_ROWS, S), VIEW_SCHEMATIC, TOP_BOARD,
                  *split_rows(BOARD_ROWS, B), VIEW_BOARD, RIGHT_END_SCHEMATIC, RIGHT_END_BOARD):
        for it in items:
            if it is SEP or it[0].startswith("@"):
                continue
            word, action = it
            pic = icon_of.get(action)
            if not pic:
                problems.append(f"{word}: KiCad gives {action} no picture; it shows blank")
                continue
            out.setdefault(pic, word)
    out.update({k: v for k, v in SHARED_PICTURE.items() if k in out})
    return out


def build_icon_pack():
    """Copy KiCad's own icon pack with our pictures in place of the ones we use."""
    import tarfile
    import tempfile
    stock = STOCK / "resources/images.tar.gz"
    svgdir = HERE.parent / "icons/svg"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        with tarfile.open(stock) as t:
            t.extractall(tmp, filter="data")
        n = 0
        for pic, word in pictures().items():
            svg = svgdir / f"{word.replace(' ', '_')}.svg"
            for size in SIZES:
                for variant in ("", "_dark"):
                    target = tmp / f"{pic}{variant}_{size}.png"
                    if not target.exists():
                        continue
                    subprocess.run(["magick", "-background", "none", "-density", str(96 * size / 24 * 4),
                                    str(svg), "-resize", f"{size}x{size}", str(target)], check=True)
                    n += 1
        res = SKIN_DATA / "resources"
        res.mkdir(parents=True, exist_ok=True)
        with tarfile.open(res / "images.tar.gz", "w:gz") as t:
            for f in sorted(tmp.iterdir()):
                t.add(f, arcname=f"./{f.name}")
    # Everything else in KiCad's data folder is linked, so upgrades flow through.
    for entry in STOCK.iterdir():
        link = SKIN_DATA / entry.name
        if entry.name != "resources" and not link.exists():
            link.symlink_to(entry)
    for entry in (STOCK / "resources").iterdir():
        link = res / entry.name
        if entry.name != "images.tar.gz" and not link.exists():
            link.symlink_to(entry)
    ENVFILE.parent.mkdir(parents=True, exist_ok=True)
    ENVFILE.write_text(f"KICAD_STOCK_DATA_HOME={SKIN_DATA}\n")
    # The menu launchers too, so it is live now rather than from the next login.
    apps = pathlib.Path.home() / ".local/share/applications"
    apps.mkdir(parents=True, exist_ok=True)
    for name in ("kicad", "eeschema", "pcbnew", "gerbview"):
        src = pathlib.Path(f"/usr/share/applications/org.kicad.{name}.desktop")
        if src.exists():
            run = f"{PATCHED}/" if HAVE_PATCHED else ""
            text = src.read_text().replace("\nExec=", f"\nExec=env KICAD_STOCK_DATA_HOME={SKIN_DATA} {run}")
            (apps / src.name).write_text(text)
    print(f"icon pack: {n} pictures replaced, in {res / 'images.tar.gz'}")


def default_board():
    """Every new project starts from KiCad's default template; give it our board."""
    target = pathlib.Path.home() / ".local/share/kicad/10.0/template/default/default.kicad_pcb"
    if not target.parent.exists():
        problems.append("KiCad's default template folder is missing; open KiCad once, then re-run")
        return
    code = (f"import pcbnew, sys; sys.path.insert(0, {str(HERE)!r}); from eaglelayers import EAGLE\n"
            f"b = pcbnew.NewBoard({str(target)!r})\n"
            "for c, n in EAGLE.items():\n"
            "    l = getattr(pcbnew, c)\n"
            "    if b.IsLayerEnabled(l): b.SetLayerName(l, n)\n"
            f"b.Save({str(target)!r})\n")
    subprocess.run(["python3", "-c", code], check=True, stderr=subprocess.DEVNULL)
    print("new projects start with Eagle layer names:", target)


def kicad_open():
    r = subprocess.run(["pgrep", "-x", "-l", "kicad|eeschema|pcbnew"], capture_output=True, text=True)
    return r.stdout.strip()


def main():
    files = {
        CFG / "toolbars/eeschema-toolbars.json": toolbars(TOP_SCHEMATIC, SCHEMATIC_ROWS, S, VIEW_SCHEMATIC, RIGHT_END_SCHEMATIC),
        CFG / "toolbars/pcbnew-toolbars.json": toolbars(TOP_BOARD, BOARD_ROWS, B, VIEW_BOARD, RIGHT_END_BOARD),
    }
    hot = "".join(f"{a}\t" + "\t".join(ks[:2]) + "\n" for a, ks in sorted(build_hotkeys().items()))

    theme = json.loads((HERE / "eagle-dark-base.json").read_text())
    theme["meta"] = {"filename": "eagle7", "name": "Eagle 7 (ours)", "version": theme["meta"]["version"]}
    merge(theme["board"], BOARD_COLOURS)
    merge(theme["schematic"], SCHEMATIC_COLOURS)
    files[CFG / "colors/eagle7.json"] = theme

    pics = pictures()
    for p in problems:
        print("!", p)
    if CHECK:
        print(f"would swap {len(pics)} KiCad pictures for ours")
        for f in files:
            print("would write", f)
        print("would write", CFG / "user.hotkeys")
        return
    if kicad_open():
        sys.exit("KiCad is open — close every KiCad window first, or it overwrites this on exit.")

    for f, data in files.items():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data, indent=2) + "\n")
        print("wrote", f)
    (CFG / "user.hotkeys").write_text(hot)
    print("wrote", CFG / "user.hotkeys")
    for app in ("eeschema", "pcbnew"):
        p = CFG / f"{app}.json"
        d = json.loads(p.read_text())
        d.setdefault("appearance", {}).update({"custom_toolbars": True, "color_theme": "eagle7"})
        d.setdefault("aui", {}).update(PANELS[app])
        # A saved window layout is restored over everything above; drop it.
        d.setdefault("window", {}).update({"perspective": "", "aui_state": None})
        p.write_text(json.dumps(d, indent=2) + "\n")
        print("set toolbars and colours in", p)
    common = CFG / "kicad_common.json"
    d = json.loads(common.read_text())
    d.setdefault("appearance", {})["icon_theme"] = 1  # dark
    d["appearance"]["toolbar_icon_size"] = ICON_SIZE
    d.setdefault("input", {}).update(MOUSE)
    common.write_text(json.dumps(d, indent=2) + "\n")
    build_icon_pack()
    default_board()
    print("\nUntil the next login, start KiCad with:\n"
          f"  KICAD_STOCK_DATA_HOME={SKIN_DATA} kicad")


if __name__ == "__main__":
    main()
