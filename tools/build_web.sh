#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GODOT_VERSION="4.7.2"
if ! BUILD_TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/bvn26-web-build.XXXXXX")"; then
  rm -f "$ROOT_DIR/dist/web/build-metadata.json" || true
  echo "Could not create the temporary Web build stage." >&2
  exit 1
fi

cleanup() {
  local exit_code=$?
  trap - EXIT
  if (( exit_code != 0 )); then
    rm -f "$ROOT_DIR/dist/web/build-metadata.json" || true
  fi
  rm -rf "$BUILD_TEMP_DIR" || true
  exit "$exit_code"
}
trap cleanup EXIT

# CI source uploads may omit .git and system variables. Fail before downloads
# rather than exporting an artifact with invented commit provenance.
python3 "$ROOT_DIR/tools/build_web_diagnostics_metadata.py" preflight --repo "$ROOT_DIR"

BUILD_LOG_ROOT="${TMPDIR:-/tmp}/bvn26-web-build-logs"
BUILD_LOG_DIR="$BUILD_LOG_ROOT/$(date -u '+%Y%m%dT%H%M%SZ')-$$"
mkdir -p "$BUILD_LOG_DIR"

ROOT_PHYSICAL="$(cd "$ROOT_DIR" && pwd -P)"
TEMP_PHYSICAL="$(cd "$BUILD_TEMP_DIR" && pwd -P)"
LOG_PHYSICAL="$(cd "$BUILD_LOG_DIR" && pwd -P)"
case "$TEMP_PHYSICAL/" in
  "$ROOT_PHYSICAL/"*)
    echo "Build staging must be outside the repository: $TEMP_PHYSICAL" >&2
    exit 1
    ;;
esac
case "$LOG_PHYSICAL/" in
  "$ROOT_PHYSICAL/"*)
    echo "Build logs must be outside the repository: $LOG_PHYSICAL" >&2
    exit 1
    ;;
esac
echo "Web build raw logs: $LOG_PHYSICAL"

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

  BUILD_TOOLS_DIR="$BUILD_TEMP_DIR/toolchain"
  mkdir -p "$BUILD_TOOLS_DIR"
  RELEASE_URL="https://github.com/godotengine/godot-builds/releases/download/${GODOT_VERSION}-stable"
  EDITOR_NAME="Godot_v${GODOT_VERSION}-stable_linux.x86_64"
  curl --fail --location --retry 3 "$RELEASE_URL/$EDITOR_NAME.zip" -o "$BUILD_TOOLS_DIR/editor.zip"
  curl --fail --location --retry 3 \
    "$RELEASE_URL/Godot_v${GODOT_VERSION}-stable_export_templates.tpz" \
    -o "$BUILD_TOOLS_DIR/templates.tpz"
  unzip -q "$BUILD_TOOLS_DIR/editor.zip" -d "$BUILD_TOOLS_DIR"

  # Keep downloads outside the project and install only the Web templates.
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
python3 "$ROOT_DIR/tools/tests/test_web_diagnostics_metadata.py"

run_godot_checked() {
  local label="$1"
  shift
  python3 "$ROOT_DIR/tools/run_godot_checked.py" \
    --log "$BUILD_LOG_DIR/$label.log" -- "$GODOT_BIN" "$@"
}

if [[ -n "${TEMPLATE_DIR:-}" ]]; then
  WEB_TEMPLATE="$TEMPLATE_DIR/web_nothreads_release.zip"
else
  case "$(uname -s)" in
    Darwin)
      TEMPLATE_ROOT="${HOME}/Library/Application Support/Godot/export_templates"
      ;;
    *)
      TEMPLATE_ROOT="${XDG_DATA_HOME:-${HOME}/.local/share}/godot/export_templates"
      ;;
  esac
  WEB_TEMPLATE="$TEMPLATE_ROOT/${GODOT_VERSION}.stable/web_nothreads_release.zip"
fi
if [[ ! -s "$WEB_TEMPLATE" ]]; then
  echo "Godot Web export template is missing or empty: $WEB_TEMPLATE" >&2
  exit 1
fi

# Freeze the complete Godot project once. All manifest generation, metadata and
# export steps below use this same snapshot; no live runtime files are reread.
STAGING_REPO="$BUILD_TEMP_DIR/repo"
PROJECT_STAGE="$STAGING_REPO/godot"
mkdir -p "$STAGING_REPO/tools" "$STAGING_REPO/services/matchmaking/src" \
  "$STAGING_REPO/evidence/online"
python3 - "$ROOT_DIR/godot" "$PROJECT_STAGE" <<'PY'
import shutil
import sys

shutil.copytree(sys.argv[1], sys.argv[2], ignore=shutil.ignore_patterns(".godot"))
PY
python3 "$ROOT_DIR/tools/bind_web_export_template.py" \
  --preset "$PROJECT_STAGE/export_presets.cfg" \
  --template "$WEB_TEMPLATE"
SNAPSHOT_TIME="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "Staged Godot source snapshot at $SNAPSHOT_TIME: $PROJECT_STAGE"

for tool in build_online_manifest.py test_online_manifest.py test_online_lobby_ui.py; do
  cp "$ROOT_DIR/tools/$tool" "$STAGING_REPO/tools/$tool"
done
mkdir -p "$STAGING_REPO/tools/importer"
cp "$ROOT_DIR/tools/importer/__init__.py" "$STAGING_REPO/tools/importer/__init__.py"
cp "$ROOT_DIR/tools/importer/visual_blend_modes.py" "$STAGING_REPO/tools/importer/visual_blend_modes.py"
cp "$ROOT_DIR/tools/importer/import_guards.py" "$STAGING_REPO/tools/importer/import_guards.py"
cp "$ROOT_DIR/tools/importer/clip_action_fields.py" "$STAGING_REPO/tools/importer/clip_action_fields.py"
cp "$ROOT_DIR/tools/importer/placement_requirements.json" "$STAGING_REPO/tools/importer/placement_requirements.json"
cp "$ROOT_DIR/tools/importer/placement_build_guard.py" "$STAGING_REPO/tools/importer/placement_build_guard.py"
cp "$ROOT_DIR/tools/importer/frame_call_guard.py" "$STAGING_REPO/tools/importer/frame_call_guard.py"
cp "$ROOT_DIR/tools/importer/form_profile_guard.py" "$STAGING_REPO/tools/importer/form_profile_guard.py"
cp "$ROOT_DIR/tools/importer/frame_call_requirements.json" "$STAGING_REPO/tools/importer/frame_call_requirements.json"
cp "$ROOT_DIR/tools/importer/visual_control_owners.json" "$STAGING_REPO/tools/importer/visual_control_owners.json"
cp "$ROOT_DIR/tools/importer/visual_control_requirements.json" "$STAGING_REPO/tools/importer/visual_control_requirements.json"
cp "$ROOT_DIR/tools/importer/visual_control_guard.py" "$STAGING_REPO/tools/importer/visual_control_guard.py"
cp "$ROOT_DIR/services/matchmaking/src/protocol.ts" "$STAGING_REPO/services/matchmaking/src/protocol.ts"
cp "$ROOT_DIR/services/matchmaking/src/catalog.json" "$STAGING_REPO/services/matchmaking/src/catalog.json"

# Build and check compatibility fingerprints only in the temporary snapshot.
python3 "$STAGING_REPO/tools/build_online_manifest.py"

EMBEDDED_METADATA="$PROJECT_STAGE/generated/build_metadata.json"
prepare_metadata() {
  python3 "$ROOT_DIR/tools/build_web_diagnostics_metadata.py" prepare \
    --repo "$ROOT_DIR" \
    --source-project "$PROJECT_STAGE" \
    --project "$PROJECT_STAGE" \
    --git-project-path godot \
    --template "$WEB_TEMPLATE" \
    --engine-version "$GODOT_VERSION"
}

# Put the resource in the project before Godot scans it, then recompute identity
# after import has generated any stable source-side .uid/.import files.
prepare_metadata

run_godot_checked import --headless --path "$PROJECT_STAGE" --editor --import --quit
# Clean CI uploads omit .import files. Import creates them, and the content
# fingerprint includes their settings, so finalize compatibility after import.
python3 "$STAGING_REPO/tools/build_online_manifest.py"
python3 "$STAGING_REPO/tools/test_online_manifest.py"
python3 "$STAGING_REPO/tools/build_online_manifest.py" --check
python3 "$STAGING_REPO/tools/test_online_lobby_ui.py"
prepare_metadata

EXPORT_STAGE="$BUILD_TEMP_DIR/export"
mkdir -p "$EXPORT_STAGE"
run_godot_checked export --headless --path "$PROJECT_STAGE" \
  --export-release Web "$EXPORT_STAGE/index.html"
# Never publish an export that changed the finalized compatibility inputs.
python3 "$STAGING_REPO/tools/build_online_manifest.py" --check

for extension in html js wasm pck; do
  test -s "$EXPORT_STAGE/index.$extension"
done

python3 "$ROOT_DIR/tools/optimize_web_pack_loader.py" "$EXPORT_STAGE/index.js"

STAGED_SIDECAR="$BUILD_TEMP_DIR/build-metadata.json"
python3 "$ROOT_DIR/tools/build_web_diagnostics_metadata.py" finalize \
  --embedded "$EMBEDDED_METADATA" \
  --pck "$EXPORT_STAGE/index.pck" \
  --output "$STAGED_SIDECAR"

# Publish the completed artifact set only after export and finalization pass.
# Keep unrelated files such as dist/web/_webrtc_transport, replace the entire
# root-level Godot export set, and copy the sidecar last.
mkdir -p "$ROOT_DIR/dist/web"
python3 - "$ROOT_DIR/dist/web" <<'PY'
import sys
from pathlib import Path

output = Path(sys.argv[1])
for path in output.iterdir():
    if path.is_file() and (path.name.startswith("index.") or path.name == "build-metadata.json"):
        path.unlink()
PY
cp -a "$EXPORT_STAGE/." "$ROOT_DIR/dist/web/"
python3 - "$ROOT_DIR/evidence/characters" "$ROOT_DIR/dist/web/evidence/characters" <<'PY'
import shutil
import sys
from pathlib import Path

# Publish retained visual evidence without shipping analysis SWFs or trace logs.
source, output = map(Path, sys.argv[1:])
for screenshot in sorted(source.glob("*/screenshots/*.png")):
    destination = output / screenshot.relative_to(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(screenshot, destination)
PY
cp "$STAGED_SIDECAR" "$ROOT_DIR/dist/web/build-metadata.json"

python3 - "$ROOT_DIR/dist/web/build-metadata.json" "$ROOT_DIR/dist/web/index.pck" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

sidecar_path, pck_path = map(Path, sys.argv[1:])
sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
hasher = hashlib.sha256()
with pck_path.open("rb") as pck:
    for chunk in iter(lambda: pck.read(1024 * 1024), b""):
        hasher.update(chunk)
digest = hasher.hexdigest()
if sidecar.get("pckSha256") != digest:
    raise SystemExit("build-metadata.json does not match dist/web/index.pck")
if not sidecar.get("gitCommit") or not sidecar.get("buildID"):
    raise SystemExit("build-metadata.json is missing build identity")
print(f"WEB_BUILD_METADATA_OK buildID={sidecar['buildID']} pckSha256={digest}")
PY
