#!/usr/bin/env python3
"""Run Godot while retaining its raw output and rejecting project errors."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_ERROR = re.compile(r"\bSCRIPT ERROR\b|\bParse Error\b")
GODOT_ERROR = re.compile(r"(?:^|\s)ERROR:")
MACOS_CA_ERROR = 'ERROR: Condition "ret != noErr" is true. Returning: ""'
MACOS_CA_LOCATION = "   at: get_system_ca_certificates (platform/macos/os_macos.mm:1035)"


def editor_settings_error(line: str) -> bool:
    return (
        "ERROR:" in line
        and "editor_settings" in line
        and ("Cannot save file" in line or "Error saving editor settings" in line)
    )


def macos_system_ca_error(lines: list[str], index: int) -> bool:
    return (
        lines[index] == MACOS_CA_ERROR
        and index + 1 < len(lines)
        and lines[index + 1] == MACOS_CA_LOCATION
    )


def run_checked(log_path: Path, command: list[str]) -> int:
    if not command:
        raise ValueError("a Godot command is required after --")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("wb") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    script_errors = [(number, line) for number, line in enumerate(lines, 1) if SCRIPT_ERROR.search(line)]
    system_warnings = [
        (number, line)
        for number, line in enumerate(lines, 1)
        if editor_settings_error(line) or macos_system_ca_error(lines, number - 1)
    ]
    other_errors = [
        (number, line)
        for number, line in enumerate(lines, 1)
        if GODOT_ERROR.search(line)
        and not SCRIPT_ERROR.search(line)
        and not editor_settings_error(line)
        and not macos_system_ca_error(lines, number - 1)
    ]

    print(f"GODOT_RAW_LOG label={log_path.stem} path={log_path} exit={result.returncode}")
    for number, line in system_warnings:
        print(f"GODOT_ENV_WARNING line={number} message={line}", file=sys.stderr)
        if line == MACOS_CA_ERROR:
            print(f"GODOT_ENV_WARNING line={number + 1} message={MACOS_CA_LOCATION}", file=sys.stderr)

    if script_errors or other_errors:
        print(
            "GODOT_LOG_SCAN_FAIL "
            f"scriptErrors={len(script_errors)} godotErrors={len(other_errors)} log={log_path}",
            file=sys.stderr,
        )
        for number, line in script_errors + other_errors:
            print(f"{log_path}:{number}:{line}", file=sys.stderr)
        return 1

    print(f"GODOT_LOG_SCAN_OK markers=none log={log_path}")
    if result.returncode != 0:
        print(f"GODOT_COMMAND_FAILED exit={result.returncode} log={log_path}", file=sys.stderr)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        return run_checked(args.log, command)
    except (OSError, ValueError) as exc:
        print(f"Godot command wrapper failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
