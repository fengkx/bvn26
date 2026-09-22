extends SceneTree

# Analysis-only probe. It exercises the real FighterRuntime source_goto_label
# implementation; it is not a native Flash or natural-input parity capture.
const OUTPUT := "res://../evidence/characters/byakuya/source-goto-lifecycle-r01/godot-runtime-r01.json"
var fighter: FighterRuntime
var rows: Array[Dictionary] = []
var failed := false

func _initialize() -> void:
	_run.call_deferred()

func _state(operation: String, extra: Dictionary = {}) -> void:
	var row := {
		"operation": operation,
		"source_frame": fighter.current_source_frame(),
		"action": fighter.action,
		"entry_serial": fighter._source_entry_serial,
		"frame_script_serial": fighter._source_frame_execution_serial,
		"pending_frames": fighter._source_goto_pending_frames.duplicate(),
		"defer_once": fighter._source_goto_defer_advance_once,
		"ai_pending": fighter._ai_pending_frames.duplicate(true),
		"display_tick": fighter.diagnostic_tick,
		"instance_local_frames": fighter._instance_local_frames.duplicate(true),
	}
	row.merge(extra, true)
	rows.append(row)

func _run() -> void:
	fighter = FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/byakuya"
	fighter.player_slot = "P1"
	fighter.diagnostic_slot = "P1"
	fighter.diagnostic_role = "analysis"
	root.add_child(fighter)
	await process_frame
	if fighter.fighter_name != "白哉":
		failed = true
		push_error("Byakuya runtime failed to initialize")
	_state("ready")

	# A -> B -> A, using the real runtime method. This remains a Godot
	# lifecycle experiment and is intentionally not called same-input parity.
	fighter.source_goto_label("站立", true, false)
	_state("goto_A")
	fighter.source_goto_label("招换", true, true)
	_state("goto_B_deferred")
	fighter.advance_ai_timeline()
	_state("dispatch_B_deferred")
	fighter.source_goto_label("站立", true, false)
	_state("goto_A_reentry")
	fighter.advance_ai_timeline()
	_state("dispatch_A_reentry")

	# Same-frame reentry on the real FighterRuntime path. The generation is
	# represented by the entry serial; no expected value is hand-written.
	fighter.source_goto_label("招换", true, false)
	var serial_before := fighter._source_entry_serial
	_state("goto_B_same_frame_1")
	fighter.source_goto_label("招换", true, false)
	var serial_after := fighter._source_entry_serial
	_state("goto_B_same_frame_2")
	if serial_after <= serial_before:
		failed = true
		push_error("same-frame source goto did not advance entry serial")

	var absolute := ProjectSettings.globalize_path(OUTPUT)
	DirAccess.make_dir_recursive_absolute(absolute.get_base_dir())
	var report := {
		"format": "bvn26-byakuya-source-goto-runtime-probe-v1",
		"status": "failed" if failed else "executed_analysis_only",
		"scope": "real Godot FighterRuntime source_goto_label lifecycle; no Flash/native parity",
		"fighter_directory": fighter.fighter_directory,
		"sequence": ["站立", "招换", "站立"],
		"rows": rows,
		"checks": {
			"same_frame_entry_serial_increased": serial_after > serial_before,
			"native_paired_capture": false,
			"natural_input_parity": false,
		},
	}
	var file := FileAccess.open(OUTPUT, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("BYAKUYA_SOURCE_GOTO_RUNTIME_" + ("FAILED" if failed else "EXECUTED") + " " + JSON.stringify(report))
	fighter.queue_free()
	await process_frame
	quit(1 if failed else 0)
