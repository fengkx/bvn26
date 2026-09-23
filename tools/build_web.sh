#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT_VERSION="4.7.2"

# Prefer an already-installed local editor. Vercel and Linux CI fall back to the
# temporary download below, so the same script works in both environments.
if [[ -n "${GODOT_BIN:-}" && "$GODOT_BIN" != */* ]]; then
  GODOT_BIN="$(command -v "$GODOT_BIN" || true)"
fi

if [[ -z "${GODOT_BIN:-}" ]]; then
  if command -v godot4 >/dev/null 2>&1; then
    GODOT_BIN="$(command -v godot4)"
  elif command -v godot >/dev/null 2>&1; then
    GODOT_BIN="$(command -v godot)"
  elif [[ -x "/Applications/Godot.app/Contents/MacOS/Godot" ]]; then
    GODOT_BIN="/Applications/Godot.app/Contents/MacOS/Godot"
  fi
fi

if [[ -z "${GODOT_BIN:-}" ]]; then
  if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
    echo "Godot $GODOT_VERSION was not found locally; install it or set GODOT_BIN." >&2
    echo "Automatic setup is available only on Linux x86_64 (including Vercel)." >&2
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

# Python smoke runners must use the same editor, including the CI download.
export GODOT_BIN

mkdir -p "$ROOT_DIR/dist/web"
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" --editor --import --quit
python3 "$ROOT_DIR/tools/build_online_manifest.py"
python3 "$ROOT_DIR/tools/test_online_manifest.py"
python3 "$ROOT_DIR/tools/build_online_manifest.py" --check
python3 "$ROOT_DIR/tools/test_online_lobby_ui.py"
"$GODOT_BIN" --headless --path "$ROOT_DIR/godot" \
  --export-release Web "$ROOT_DIR/dist/web/index.html"

for extension in html js wasm pck; do
  test -s "$ROOT_DIR/dist/web/index.$extension"
done
