#!/usr/bin/env bash
# Make KiCad 10 look and work like Eagle 7.
#
#   ./install.sh                 everything: patched KiCad build + Eagle settings
#   ./install.sh --settings-only  only the settings, icons and launchers, on the
#                                 KiCad you already have (no Eagle mouse, no
#                                 two-wide column, no command-then-click)
#
# Close KiCad first: it rewrites its settings when it exits.
#
# The patched KiCad is built from the official 10.0.6 source and installed in
# ~/.local/opt/kicad-eagle, beside the official KiCad, which is left untouched.
# KiCad's menu launchers in your home folder are pointed at it. To go back,
# delete ~/.local/share/applications/org.kicad.*.desktop.
#
# Written for Fedora. Elsewhere, install KiCad's build requirements your own
# way and run with SKIP_DEPS=1.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
KICAD_TAG="10.0.6"
PREFIX="$HOME/.local/opt/kicad-eagle"
WORK="${WORK:-$HOME/.cache/kicad-eagle-build}"

say() { printf '\n== %s\n' "$*"; }

if pgrep -x -l "kicad|eeschema|pcbnew" >/dev/null; then
    echo "KiCad is open. Close every KiCad window, then run this again." >&2
    exit 1
fi

for tool in python3 magick; do
    command -v "$tool" >/dev/null || { echo "Needs $tool (ImageMagick for magick)." >&2; exit 1; }
done
python3 -c "import pcbnew" 2>/dev/null || {
    echo "Needs KiCad 10 installed with its Python module (Fedora: the kicad package)." >&2; exit 1; }

if [[ "${1:-}" != "--settings-only" ]]; then
    if [[ "${SKIP_DEPS:-0}" != "1" ]]; then
        say "Installing what KiCad needs to compile (asks for your password)"
        sudo dnf builddep -y kicad
    fi

    say "Fetching KiCad $KICAD_TAG"
    mkdir -p "$WORK"
    if [[ ! -d "$WORK/src" ]]; then
        git clone --depth 1 --branch "$KICAD_TAG" https://gitlab.com/kicad/code/kicad.git "$WORK/src"
    fi
    git -C "$WORK/src" checkout -q -- .
    git -C "$WORK/src" apply "$HERE/patches/0001-eagle.patch"

    say "Building (the first build takes a while)"
    cmake -S "$WORK/src" -B "$WORK/build" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$PREFIX" -DKICAD_BUILD_QA_TESTS=OFF -DKICAD_BUILD_I18N=OFF \
        -DKICAD_SPICE_QA=OFF >/dev/null
    nice ninja -C "$WORK/build"
    ninja -C "$WORK/build" install >/dev/null

    # The patched build looks for part libraries under its own prefix; use the
    # ones installed with the official KiCad.
    for d in symbols footprints 3dmodels; do
        [[ -e "$PREFIX/share/kicad/$d" || ! -e "/usr/share/kicad/$d" ]] || ln -s "/usr/share/kicad/$d" "$PREFIX/share/kicad/$d"
    done
fi

say "Drawing the icons"
python3 "$HERE/icons/make_icons.py" >/dev/null

say "Writing the Eagle settings"
python3 "$HERE/setup/apply.py"

say "Done"
echo "Open KiCad from the menu. Existing boards keep KiCad's layer names; to give one"
echo "Eagle's names (close it first):"
echo "  python3 $HERE/setup/eaglelayers.py <board>.kicad_pcb"
