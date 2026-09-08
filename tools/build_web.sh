#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT_VERSION="4.7.2"

# A local editor override uses its already-installed matching export templates.
if [[ -z "${GODOT_BIN:-}" ]]; then
  if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
    echo "Automatic setup requires Linux x86_64; set GODOT_BIN for a local editor." >&2
    exit 1
  fi

  BUILD_TOOLS_DIR="$(mktemp -d)"
  trap 'rm -rf "$BUILD_TOOLS_DIR"' EXIT
  RELEASE_URL="https://github.com/godotengine/godot-builds/releases/download/${GODOT_VERSION}-stable"
  EDITOR_NAME="Godot_v${GODOT_VERSION}-stable_linux.x86_64"
  curl --fail --location --retry 3 "$RELEASE_URL/$EDITOR_NAME.zip" -o "$BUILD_TOOLS_DIR/editor.zip"
  curl --fail --location --retry 3 \
    "$RELEASE_URL/Godot_v${GODOT_VERSION}-stable_export_templates.tpz" \
    -o "$BUILD_TOOLS_DIR/templates.tpz"
  unzip -q "$BUILD_TOOLS_DIR/editor.zip" -d "$BUILD_TOOLS_DIR"

  # Keep tool downloads outside the project and install only the Web templates.
  export XDG_DATA_HOME="$BUILD_TOOLS_DIR/data"
  TEMPLATE_DIR="$XDG_DATA_HOME/godot/export_templates/${GODOT_VERSION}.stable"
  mkdir -p "$TEMPLATE_DIR"
  unzip -j -q "$BUILD_TOOLS_DIR/templates.tpz" \
    'templates/web_nothreads_release.zip' 'templates/web_nothreads_debug.zip' \
    'templates/version.txt' -d "$TEMPLATE_DIR"
  GODOT_BIN="$BUILD_TOOLS_DIR/$EDITOR_NAME"
  chmod +x "$GODOT_BIN"
fi

case "$("$GODOT_BIN" --version)" in
  "$GODOT_VERSION.stable."*) ;;
  *) echo "Expected Godot $GODOT_VERSION stable." >&2; exit 1 ;;
esac

mkdir -p "$ROOT_DIR/dist/web"
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --editor --import --quit
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" \
  --export-release Web "$ROOT_DIR/dist/web/index.html"

for extension in html js wasm pck; do
  test -s "$ROOT_DIR/dist/web/index.$extension"
done
