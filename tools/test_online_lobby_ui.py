#!/usr/bin/env python3
"""Run the native online lobby interaction and viewport smoke test."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GODOT_DEFAULTS = (
    "/private/tmp/bvn-godot-toolchain/Godot.app/Contents/MacOS/Godot",
    "/Applications/Godot.app/Contents/MacOS/Godot",
)


def find_godot() -> str:
    configured = os.environ.get("GODOT_BIN")
    if configured:
        return configured if "/" in configured else shutil.which(configured) or configured
    for candidate in GODOT_DEFAULTS:
        if Path(candidate).is_file():
            return candidate
    return shutil.which("godot4") or shutil.which("godot") or "godot"


def main() -> int:
    godot = find_godot()
    cases = (
        (
            "res://tests/online_lobby_ui_smoke.gd",
            (
                "ONLINE_LOBBY_UI_SMOKE_OK owner_setup_draft_preserved=true map_picker_not_dropdown=true role_dropdowns_absent=true dialog_fits=true",
                "ONLINE_LOBBY_REENTRY_SMOKE_OK open_mouse_close_reopen_escape=true",
                "ONLINE_LOBBY_CANCEL_SMOKE_OK mouse_cancel=true delayed_prepare_ignored=true generation_guard=true phase_locked=true retry_success=true local_abandon=true no_remote_leave=true",
                "ONLINE_LOBBY_RENDER_SURFACE_SMOKE_OK mouse_close=true escape_close=true reentry=true fixed_footer=true abandon=true",
            ),
        ),
        (
            "res://tests/title_menu_online_entry_smoke.gd",
            (
                "TITLE_MENU_ONLINE_SMOKE_OK cycle_down=true cycle_up=true signal_entry=true keyboard_confirmation=true reset=true",
            ),
        ),
        (
            "res://tests/online_character_selection_smoke.gd",
            (
                "ONLINE_CHARACTER_SELECTION_SMOKE_OK local_slots=true phase_barrier=true helper_phase=true choice_freeze=true buffered_phase_validation=true service_ids=true offline_chain_isolated=true",
                "ONLINE_CHARACTER_SELECTION_RESELECT_SMOKE_OK stale_session_rejected=true cancel_keeps_choice=true",
                "ONLINE_CHARACTER_SELECTION_LIFECYCLE_SMOKE_OK pending_timer_stopped=true teardown_rejects_late_snapshot=true reentry=true",
                "ONLINE_CHARACTER_SELECTION_SOURCE_RULE_SMOKE_OK same_fighter_helper_rejected=true invalid_old_helper_not_restored=true",
            ),
        ),
        (
            "res://tests/online_map_selection_smoke.gd",
            (
                "ONLINE_MAP_SELECTION_OK: host-only input, mirrored snapshots, confirmed/cancelled lifecycle, stale-session rejection",
            ),
        ),
        (
            "res://tests/online_lobby_map_selection_integration_smoke.gd",
            (
                "ONLINE_LOBBY_MAP_SELECTION_INTEGRATION_SMOKE_OK network_authority=true guest_read_only=true push_before_http=true profile_change_clears_ready=true uncertain_exact_retry=true map_preserves_profile=true host_authority=true guest_mirror=true map_commit_handshake=true rules_draft=true null_profiles_ready=true auto_prepare_gated=true auto_prepare_deduplicated=true explicit_retry=true cancel_and_reentry=true guest_pending_snapshot=true host_refresh_failure_returns=true guest_refresh_retry=true",
            ),
        ),
        (
            "res://tests/online_lobby_selection_integration_smoke.gd",
            (
                "ONLINE_LOBBY_SELECTION_INTEGRATION_SMOKE_OK two_lobbies=true original_view=true one_local_slot=true peer_snapshot=true refresh_preserves_draft=true dropdowns_absent=true select_order=true push_before_http_reply=true commits_acknowledged=true map_follows_roles=true ready_gated_until_map=true same_choice_reselect=true ready_start_gated=true busy_restored=true profile_change_disconnect=true room_hidden=true cancel_both=true inactive_end_idempotent=true physics_end_idempotent=true reentry=true",
            ),
        ),
        (
            "res://tests/online_room_client_smoke.gd",
            (
                "ONLINE_ROOM_CLIENT_SMOKE_OK state_validation=true network_profile_validation=true server_upgrade_required=true cloudflare_ice=true ice_transport_chain=true string_urls_normalized=true turn_credentials_required=true monotonic_revision=true leave_projection=true exact_retry=true short_code_join=true create_code=true reinvite_retry=true",
            ),
        ),
    )
    for script, markers in cases:
        frame_budget = "1500" if script == "res://tests/online_lobby_selection_integration_smoke.gd" else "500"
        command = [
            godot,
            "--headless",
            "--path",
            str(ROOT / "godot"),
            "--script",
            script,
            "--quit-after",
            frame_budget,
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        output = result.stdout + result.stderr
        sys.stdout.write(output)
        failures = []
        if result.returncode != 0:
            failures.append(f"Godot exited with status {result.returncode}")
        for marker in markers:
            if marker not in output:
                failures.append(f"success marker was missing: {marker}")
        if "SCRIPT ERROR" in output or "Assertion failed" in output:
            failures.append("Godot reported a script error or failed assertion")
        if failures:
            print(f"Online UI smoke failed for {script}: " + "; ".join(failures), file=sys.stderr)
            return 1
    print("ONLINE_LOBBY_UI_RUNNER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
