"""Build comparable Web packs for the existing DOM-reporting rollback profile."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence/online/performance-30hz"
PROFILE_PROJECT = Path("/private/tmp/bvn-lag-web-profile")
PROFILE = ROOT / "godot/tests/rollback_performance_profile.gd"
USER_TAPE = ROOT / "godot/tests/rollback_performance_user_log_r01.json"
PROFILE_MARKER = "LAG_PROFILE "
KNOWN_ENVIRONMENT_DIAGNOSTICS = (
    'ERROR: Condition "ret != noErr" is true. Returning:',
    "ERROR: Cannot save file '/Users/fengkx/Library/Application Support/Godot/editor_settings-4.7.tres'.",
    "ERROR: Error saving editor settings to /Users/fengkx/Library/Application Support/Godot/editor_settings-4.7.tres",
    "ERROR: 3 RID allocations of type 'P12GodotBody3D' were leaked at exit.",
    "ERROR: 2 resources still in use at exit (run with --verbose for details).",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_for(source: Path) -> dict:
    resolved = source.resolve()
    for path in EVIDENCE.glob("*.json"):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("frozen_copy") == str(resolved):
            return {"path": str(path.relative_to(ROOT)), **manifest}
    return {"path": None, "frozen_copy": str(resolved)}


def run_logged(command: list[str], log_path: Path, timeout: int = 180) -> dict:
    started = time.perf_counter()
    engine_log = log_path.with_name(f"{log_path.stem}-godot.log")
    command = [command[0], "--log-file", str(engine_log), *command[1:]]
    result = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    elapsed = time.perf_counter() - started
    console_output = result.stdout + result.stderr
    engine_output = engine_log.read_text(encoding="utf-8", errors="replace") if engine_log.exists() else ""
    output = console_output + "\n--- Godot --log-file ---\n" + engine_output
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output, encoding="utf-8")
    unexpected_errors = [
        line for line in output.splitlines()
        if "ERROR:" in line and not any(allowed in line for allowed in KNOWN_ENVIRONMENT_DIAGNOSTICS)
    ]
    hard_errors = [
        line for line in output.splitlines()
        if any(token in line for token in ("SCRIPT ERROR", "Parse Error", "Assertion failed"))
    ]
    if result.returncode != 0 or unexpected_errors or hard_errors:
        raise RuntimeError(
            f"Command failed; exit={result.returncode}; unexpected={unexpected_errors}; "
            f"parse/assert={hard_errors}; log={log_path}\n{output[-6000:]}"
        )
    return {
        "command": command,
        "exit_code": result.returncode,
        "wall_seconds": elapsed,
        "log": str(log_path),
        "godot_log": str(engine_log),
        "known_environment_diagnostics": [
            line for line in output.splitlines()
            if any(allowed in line for allowed in KNOWN_ENVIRONMENT_DIAGNOSTICS)
        ],
    }


def web_profile_script() -> str:
    source = PROFILE.read_text(encoding="utf-8")

    def replace_once(old: str, new: str) -> None:
        nonlocal source
        if old not in source:
            raise RuntimeError(f"Could not apply Web profile transform: {old!r}")
        source = source.replace(old, new, 1)

    replace_once("extends SceneTree", "extends Node")
    replace_once("var _scenario := \"default\"", "var _scenario := \"user-log-r01\"")
    replace_once(
        "func _initialize() -> void:\n\t_run.call_deferred()",
        "func _ready() -> void:\n\tcall_deferred(\"_run\")",
    )
    source = source.replace("Fixture.create(self", "Fixture.create(get_tree()")
    source = source.replace("await process_frame", "await get_tree().process_frame")
    source = source.replace("quit(1)", "get_tree().quit(1)")
    replace_once("\tquit()\n", "\t_write_web_report()\n")
    replace_once(
        "\t\tprint(\"ROLLBACK_PERFORMANCE \", JSON.stringify(report))",
        "\t\t_web_reports.append(report)",
    )
    replace_once("var _reference_state := {}", "var _reference_state := {}\nvar _web_reports: Array[Dictionary] = []")
    replace_once(
        "func _check(problem: String) -> bool:\n\tif not problem.is_empty():\n\t\tpush_error(problem)\n\t\treturn false\n\treturn true",
        "func _check(problem: String) -> bool:\n"
        "\tif problem.is_empty():\n\t\treturn true\n"
        "\tpush_error(problem)\n"
        "\tvar error_report := {\"schemaVersion\": 1, \"status\": \"error\", \"message\": problem}\n"
        "\tJavaScriptBridge.eval(\"document.getElementById('report').textContent = \" + JSON.stringify(JSON.stringify(error_report, \"  \")))\n"
        "\tget_tree().quit(1)\n"
        "\treturn false",
    )
    source += '''


func _write_web_report() -> void:
\tvar config: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://tests/rollback_performance_web_config.json"))
\tif not config is Dictionary:
\t\t_check("Missing Web performance source configuration")
\t\treturn
\tvar browser_raw: Variant = JavaScriptBridge.eval("JSON.stringify({userAgent:navigator.userAgent,hardwareConcurrency:navigator.hardwareConcurrency||null,visibility:document.visibilityState,devicePixelRatio:window.devicePixelRatio,screenWidth:screen.width,screenHeight:screen.height})")
\tvar browser: Variant = JSON.parse_string(str(browser_raw))
\tvar report := {
\t\t"schemaVersion": 1,
\t\t"kind": "bvn-online-performance-web-burst",
\t\t"status": "complete",
\t\t"pairId": config.pair_id,
\t\t"source": config.source_label,
\t\t"sourceFingerprint": config.source_fingerprint,
\t\t"sourceFiles": config.source_files,
\t\t"fixture": {"id": "user-log-r01", "inputTapeSha256": config.input_tape_sha256, "recordedTicks": [28, 249], "neutralPaddingOnly": [[1, 27], [250, 330]]},
\t\t"randomSeed": 727,
\t\t"introSchedule": "poll every 15 ticks; skip intro ticks 30-89",
\t\t"engine": Engine.get_version_info(),
\t\t"browser": browser if browser is Dictionary else {"userAgent": str(browser_raw)},
\t\t"cadenceMeasured": false,
\t\t"measurements": _web_reports,
\t}
\tvar report_text := JSON.stringify(report, "  ")
\tJavaScriptBridge.eval("document.getElementById('report').textContent = " + JSON.stringify(report_text))
'''
    return source


def prepare_project(godot: str, label: str, source: Path, stage: Path, log_dir: Path, harness: Path) -> dict:
    source = source.resolve()
    project = stage / "projects" / label / "godot"
    pack = stage / "packs" / label / "index.pck"
    if project.exists() and pack.is_file() and pack.stat().st_size > 0:
        preflight = {"reused": True, "log": str(log_dir / f"{label}-import.log")}
        export = {"reused": True, "log": str(log_dir / f"{label}-export-pack.log")}
    else:
        project.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["cp", "-cR", str(source), str(project)], check=True)
        web_profile = project / "tests/rollback_performance_web_profile.gd"
        web_profile.write_text(web_profile_script(), encoding="utf-8")
        web_scene = project / "tests/rollback_performance_web_profile.tscn"
        web_scene.write_text(
            '[gd_scene load_steps=2 format=3]\n\n'
            '[ext_resource type="Script" path="res://tests/rollback_performance_web_profile.gd" id="1"]\n\n'
            '[node name="RollbackPerformanceWebProfile" type="Node"]\n'
            'script = ExtResource("1")\n',
            encoding="utf-8",
        )
        shutil.copy2(USER_TAPE, project / "tests/rollback_performance_user_log_r01.json")
        source_manifest = manifest_for(source)
        profile_config = {
            "schemaVersion": 1,
            "pair_id": ARGS.pair_id,
            "source_label": label,
            "source_fingerprint": source_manifest.get("tree_sha256"),
            "source_files": {
                "battle_checkpoint_sha256": sha256(source / "battle_checkpoint.gd"),
                "main_sha256": sha256(source / "main.gd"),
            },
            "input_tape_sha256": sha256(USER_TAPE),
            "candidate_url": f"http://127.0.0.1:{ARGS.port}/candidate/index.html",
        }
        (project / "tests/rollback_performance_web_config.json").write_text(
            json.dumps(profile_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        project_file = project / "project.godot"
        config = project_file.read_text(encoding="utf-8")
        config, replaced = re.subn(
            r'(?m)^run/main_scene=.*$',
            'run/main_scene="res://tests/rollback_performance_web_profile.tscn"',
            config,
            count=1,
        )
        if replaced != 1:
            raise RuntimeError(f"Could not select profile scene in {project_file}")
        project_file.write_text(config, encoding="utf-8")

        preflight = run_logged(
            [godot, "--headless", "--editor", "--path", str(project), "--quit"],
            log_dir / f"{label}-import.log",
            timeout=900,
        )
        pack.parent.mkdir(parents=True, exist_ok=True)
        export = run_logged(
            [godot, "--headless", "--path", str(project), "--export-pack", "Web", str(pack)],
            log_dir / f"{label}-export-pack.log",
            timeout=900,
        )
    if not pack.is_file() or pack.stat().st_size == 0:
        raise RuntimeError(f"Web pack export did not create {pack}")

    web_dir = stage / "www" / label
    web_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "index.html",
        "index.js",
        "index.wasm",
        "index.audio.worklet.js",
        "index.audio.position.worklet.js",
    ):
        shutil.copy2(harness / "web" / name, web_dir / name)
    shutil.copy2(pack, web_dir / "index.pck")
    html_path = web_dir / "index.html"
    html = html_path.read_text(encoding="utf-8")
    match = re.search(r"const GODOT_CONFIG = (\{.*?\});", html, flags=re.DOTALL)
    if match is None:
        raise RuntimeError("Full Web shell did not contain a GODOT_CONFIG object")
    engine_config = json.loads(match.group(1))
    engine_config.setdefault("fileSizes", {})["index.pck"] = pack.stat().st_size
    html = html[:match.start(1)] + json.dumps(engine_config, separators=(",", ":")) + html[match.end(1):]
    html_path.write_text(html, encoding="utf-8")

    source_manifest = manifest_for(source)
    return {
        "label": label,
        "source": str(source),
        "source_manifest": source_manifest.get("path"),
        "parent_tree_sha256": source_manifest.get("tree_sha256"),
        "battle_checkpoint_sha256": sha256(source / "battle_checkpoint.gd"),
        "profile_sha256": hashlib.sha256(web_profile_script().encode("utf-8")).hexdigest(),
        "pck_sha256": sha256(pack),
        "pck_bytes": pack.stat().st_size,
        "web_shell_sha256": sha256(html_path),
        "web_engine_js_sha256": sha256(web_dir / "index.js"),
        "web_engine_wasm_sha256": sha256(web_dir / "index.wasm"),
        "web_audio_worklet_sha256": sha256(web_dir / "index.audio.worklet.js"),
        "web_audio_position_worklet_sha256": sha256(web_dir / "index.audio.position.worklet.js"),
        "import": preflight,
        "export_pack": export,
        "url": f"http://127.0.0.1:{ARGS.port}/{label}/index.html",
    }


def start_server(stage: Path, port: int, log_dir: Path) -> dict:
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            raise RuntimeError(f"Port {port} is already in use; choose another --port")
    server_log = log_dir / "http-server.log"
    handle = server_log.open("wb")
    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(stage / "www")],
        stdin=subprocess.DEVNULL,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    handle.close()
    for _ in range(40):
        if process.poll() is not None:
            raise RuntimeError(f"HTTP server exited; see {server_log}")
        with socket.socket() as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                return {"pid": process.pid, "port": port, "log": str(server_log)}
        time.sleep(0.1)
    process.terminate()
    raise RuntimeError(f"HTTP server did not become ready; see {server_log}")


def main() -> None:
    global ARGS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", required=True, help="Godot 4.7.2 executable")
    parser.add_argument("--baseline", type=Path, required=True, help="Frozen baseline godot/ directory")
    parser.add_argument("--candidate", type=Path, required=True, help="Frozen or source-locked candidate godot/ directory")
    parser.add_argument("--harness", type=Path, default=PROFILE_PROJECT, help="Previously validated full-shell Web profile project")
    parser.add_argument("--stage", type=Path, default=Path("/private/tmp/bvn26-web-performance-r02"))
    parser.add_argument("--log-dir", type=Path, default=Path("/private/tmp/bvn26-web-performance-logs-r02"))
    parser.add_argument("--report", type=Path, default=EVIDENCE / "web-build-r02.json")
    parser.add_argument("--port", type=int, default=8037)
    parser.add_argument("--pair-id", default="user-log-r01-web-final-20260924")
    parser.add_argument("--no-serve", action="store_true", help="Prepare matched web directories without starting the HTTP server")
    ARGS = parser.parse_args()

    godot_version = subprocess.run([ARGS.godot, "--version"], check=True, text=True, capture_output=True, timeout=15).stdout.strip()
    if not godot_version.startswith("4.7.2"):
        raise RuntimeError(f"Expected Godot 4.7.2, got {godot_version}")
    for path in (ARGS.baseline, ARGS.candidate, ARGS.harness):
        if not path.is_dir():
            raise RuntimeError(f"Missing directory: {path}")
    ARGS.stage.mkdir(parents=True, exist_ok=True)
    ARGS.log_dir.mkdir(parents=True, exist_ok=True)
    results = [
        prepare_project(ARGS.godot, "baseline", ARGS.baseline, ARGS.stage, ARGS.log_dir, ARGS.harness),
        prepare_project(ARGS.godot, "candidate", ARGS.candidate, ARGS.stage, ARGS.log_dir, ARGS.harness),
    ]
    server = None if ARGS.no_serve else start_server(ARGS.stage, ARGS.port, ARGS.log_dir)
    report = {
        "status": "packs_ready_waiting_for_visible_browser_capture",
        "scope": "Same-machine Godot Web burst profile; DOM output is not a real-time 30 Hz paired-match pass.",
        "godot": godot_version,
        "profile": "Transformed copy of the native rollback_performance_profile.gd; user-log-r01 330-tick fixture; result JSON is written into #report",
        "browser_procedure": "Open baseline URL in one visible tab, capture its #report JSON, then navigate the same tab to candidate URL. Run one page at a time; this is burst timing, not a real-time cadence test.",
        "dom_result_schema": {"container": "#report", "schemaVersion": 1, "kind": "bvn-online-performance-web-burst"},
        "harness_source": str(ARGS.harness.resolve()),
        "source_comparison": results,
        "server": server,
    }
    ARGS.report.parent.mkdir(parents=True, exist_ok=True)
    ARGS.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ARGS = None
    main()
