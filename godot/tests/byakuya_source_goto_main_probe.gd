extends SceneTree

# Analysis-only main-scene probe. It uses the real battle bootstrap and
# SourceCallbackRegistry, then injects one controlled source goto. It is not
# natural-input parity evidence.
const OUTPUT := "res://../evidence/characters/byakuya/source-goto-lifecycle-r01/godot-main-r01.json"
var game: Node
var fighter: FighterRuntime
var rows: Array[Dictionary] = []
var frame_script_events: Array[Dictionary] = []
var fight_start_tick := -1

func _initialize() -> void:
	_run.call_deferred()

func _input_tape(_slot: String, _tick: int) -> Dictionary:
	return {"up": false, "down": false, "left": false, "right": false,
		"attack": false, "jump": false, "dash": false, "ranged": false,
		"special": false, "summon": false}

func _record(operation: String, extra: Dictionary = {}) -> void:
	var row := {
		"operation": operation,
		"physics_tick": game.physics_tick,
		"relative_fight_tick": game.physics_tick - fight_start_tick,
		"registry_tick": game.source_callbacks.current_tick if game.source_callbacks != null else -1,
		"registry_size": game.source_callbacks.size() if game.source_callbacks != null else -1,
		"source_frame": fighter.current_source_frame(),
		"action": fighter.action,
		"entry_serial": fighter._source_entry_serial,
		"frame_script_serial": fighter._source_frame_execution_serial,
		"pending_goto": fighter._source_goto_pending_frames.duplicate(),
		"defer_once": fighter._source_goto_defer_advance_once,
		"ai_pending": fighter._ai_pending_frames.duplicate(true),
		"instance_local_frames": fighter._instance_local_frames.duplicate(true),
	}
	row.merge(extra, true)
	rows.append(row)

func _on_frame_script_boundary(frame: int, entering: bool) -> void:
	frame_script_events.append({
		"physics_tick": game.physics_tick,
		"relative_fight_tick": game.physics_tick - fight_start_tick,
		"source_frame": frame,
		"entering": entering,
	})

func _controlled_goto(label: String, operation: String) -> void:
	fighter.source_goto_label(label, true, false)
	_record(operation, {"goto_label": label, "goto_mode": "same_tick_controlled"})

func _run() -> void:
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	game._on_menu_confirmed("vs_com")
	game.character_selection.available.fighters["白哉"] = "byakuya"
	game._on_characters_confirmed(["白哉", "一护"], ["魂", "魂"])
	game._on_map_confirmed("现世")
	game.diagnostic_input_provider = Callable(self, "_input_tape")
	fighter = game.naruto
	fighter.source_frame_script_boundary.connect(_on_frame_script_boundary)
	var reached_ready := false
	for _tick in 900:
		if not game.battle_intro.active and fight_start_tick < 0:
			fight_start_tick = game.physics_tick
			fighter.source_x = 300.0
			fighter.source_y = -25.0
			game.ichigo.source_x = 350.0
			game.ichigo.source_y = -25.0
			fighter.sync_body_collision_position()
			game.ichigo.sync_body_collision_position()
			fighter.energy = 300.0
			game.ichigo.energy = 300.0
			reached_ready = true
			break
		game._advance_fight()
	assert(reached_ready, "main bootstrap did not reach Ready")
	_record("ready_before_injection")

	# Same-callback A->B->A and repeated B->B are explicit AVM semantic
	# experiments. They are kept separate from natural-input parity.
	_controlled_goto("站立", "sync_A0")
	_controlled_goto("招换", "sync_B0")
	_controlled_goto("站立", "sync_A1")
	_controlled_goto("站立", "sync_repeat_A")
	_controlled_goto("招换", "sync_repeat_B0")
	_controlled_goto("招换", "sync_repeat_B1")
	_controlled_goto("站立", "sync_final_A")
	# Cross-display A->B->A: one real main-loop advance between labels.
	_controlled_goto("站立", "cross_A")
	game._advance_fight()
	_record("cross_tick_after_A")
	_controlled_goto("招换", "cross_B")
	game._advance_fight()
	_record("cross_tick_after_B")
	_controlled_goto("站立", "cross_A2")
	game._advance_fight()
	_record("cross_tick_after_A2")

	var absolute := ProjectSettings.globalize_path(OUTPUT)
	DirAccess.make_dir_recursive_absolute(absolute.get_base_dir())
	var report := {
		"format": "bvn26-byakuya-source-goto-main-runtime-probe-v1",
		"status": "executed_analysis_only",
		"scope": "real main.tscn bootstrap plus SourceCallbackRegistry with one controlled goto; not native parity",
		"fixture": {"p1": "白哉", "p2": "一护", "p1_helper": "魂", "p2_helper": "魂", "stage": "现世"},
		"sequence": ["站立", "招换"],
		"fight_start_tick": fight_start_tick,
		"rows": rows,
		"frame_script_events": frame_script_events,
		"natural_input_parity": false,
	}
	var file := FileAccess.open(OUTPUT, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("BYAKUYA_SOURCE_GOTO_MAIN_" + JSON.stringify(report))
	game.queue_free()
	await process_frame
	quit()
