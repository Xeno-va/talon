#!/usr/bin/env python3
"""Give a KiCad board Eagle 7's layer names.

    python3 setup/eaglelayers.py <board.kicad_pcb>            rename, then save
    python3 setup/eaglelayers.py <board.kicad_pcb> --check    say what would change
    python3 setup/eaglelayers.py <board.kicad_pcb> --undo     back to KiCad's names

Only the names shown on screen change. The layers themselves, and everything on
them, stay exactly where they are: KiCad's own code loads the board, sets each
name and saves it, so no part, track or zone can move. Fabrication files still
say which layer they are by its fixed identity inside the file, so a fab house
reads them the same. KiCad's own plot dialog does name its output files after
these names (board-Top.gbr instead of board-F_Cu.gbr).

Close the board in KiCad first, or KiCad's next save puts the old names back.
"""
import shutil
import sys

import pcbnew

# Eagle 7 layer names, from its manual's layer table. Eagle has no counterpart
# for KiCad's margin, Eco and User layers, so those keep KiCad's names.
EAGLE = {
    "F_Cu": "Top", "B_Cu": "Bottom",
    "F_SilkS": "tPlace", "B_SilkS": "bPlace",
    "F_Mask": "tStop", "B_Mask": "bStop",
    "F_Paste": "tCream", "B_Paste": "bCream",
    "F_Adhes": "tGlue", "B_Adhes": "bGlue",
    "F_CrtYd": "tKeepout", "B_CrtYd": "bKeepout",
    "F_Fab": "tDocu", "B_Fab": "bDocu",
    "Edge_Cuts": "Dimension",
    "Dwgs_User": "Document",
    "Cmts_User": "Measures",
}
EAGLE.update({f"In{n}_Cu": f"Route{n + 1}" for n in range(1, 15)})  # Route2 .. Route15


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    path, check, undo = sys.argv[1], "--check" in sys.argv, "--undo" in sys.argv
    board = pcbnew.LoadBoard(path)
    changes = []
    for const, eagle in EAGLE.items():
        layer = getattr(pcbnew, const)
        if not board.IsLayerEnabled(layer):
            continue
        want = "" if undo else eagle
        now = board.GetLayerName(layer)
        std = board.GetStandardLayerName(layer)
        if (undo and now != std) or (not undo and now != eagle):
            changes.append((layer, std, now, want))
    for _, std, now, want in changes:
        print(f"  {std:12} {now:16} -> {want or std}")
    if not changes:
        print("nothing to change")
        return
    if check:
        return
    shutil.copy2(path, path + ".before-eagle-names")
    for layer, _, _, want in changes:
        if not board.SetLayerName(layer, want):
            sys.exit(f"KiCad refused the name {want!r}; board not saved")
    board.Save(path)
    print(f"saved; the original is beside it as {path}.before-eagle-names")


if __name__ == "__main__":
    main()
