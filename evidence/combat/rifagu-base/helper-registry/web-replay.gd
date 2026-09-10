extends Node

var game
var fixture: Dictionary
var mode: int
var rows: Array = []
var presentation_rows: Array = []
var recovery_events: Dictionary = {}

func _ready() -> void:
	_run.call_deferred()

func _run() -> void:
	await _run_case("res://air_target.json", "user://air_target.json")
	await _run_case("res://held.json", "user://held.json")
	print("HELPER_WEB_REPLAY_OK")


func _run_case(fixture_path: String, output_path: String) -> void:
	rows = []
	presentation_rows = []
	recovery_events = {}
	fixture = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	mode = 3
	game = load("res://main.tscn").instantiate()
	get_tree().root.add_child(game)
	game.set_physics_process(false)
	game.recorded_training_timers = true
	if fixture.has("fighters"):
		var names: Array = []
		for slot in ["p1", "p2"]:
			var found := ""
			for label in game.character_selection.available.fighters:
				if game.character_selection.available.fighters[label] == fixture.fighters[slot]:
					found = label
			assert(not found.is_empty())
			names.append(found)
		game._replace_selected_actors(names, ["我爱罗", "魂"])
		game._load_selected_stage("现世")
	game._enter_current_fight(mode)
	for tick in 700:
		game._advance_fight([], func() -> bool:
			if not game.battle_intro.active: _observe(0)
			return false)
		if not game.battle_intro.active: break
	assert(not game.battle_intro.active and rows.size() == 2)
	for tick in range(1, int(fixture.frames) + 1):
		game._advance_fight(recovery_events.get(tick, []), func() -> bool:
			_observe(tick)
			return false)
	FileAccess.open(output_path, FileAccess.WRITE).store_string(JSON.stringify(rows, "", true, true))
	FileAccess.open(output_path + ".presentation.json", FileAccess.WRITE).store_string(JSON.stringify(presentation_rows, "", true, true))
	print("HELPER_WEB_HASH ", fixture.id, " ", JSON.stringify(rows, "", true, true).sha256_text())
	game._goto_menu()
	game.queue_free()
	await get_tree().process_frame
	print("MOVE_CASE_REFERENCE_OK ", fixture.id)

func _observe(tick: int) -> void:
	presentation_rows.append({"tick": tick, "x": game.position.x, "y": game.position.y})
	if tick == 0:
		for actor in [game.naruto, game.ichigo]:
			var setup: Dictionary = fixture.setup[actor.player_slot]
			actor.goto_ai_label("站立", true)
			actor.position.x = setup.x
			actor.energy = setup.energy
	for actor in [game.naruto, game.ichigo]:
		rows.append({"tick": tick, "slot": actor.player_slot, "frame": actor.current_source_frame(),
			"x": actor.source_x, "y": actor.source_y, "xscale": actor.scale.x * 100,
			"action": actor.ai_source_state.read_field("动作"), "hp": actor.health,
			"ql": actor.energy, "sw": actor.sw, "touch": actor.ai_source_state.read_field("touch"),
			"touchFloor": actor.ai_source_state.read_field("touchFloor"), "hits": actor.hits,
			"paused": actor.root_zhanting, "hstm": actor.ai_source_state.read_field("hstm"),
			"hurtSkling": actor.ai_source_state.read_field("hurtSkling")})
	var bindings := {
		"p1": {"up": KEY_W, "down": KEY_S, "left": KEY_A, "right": KEY_D,
			"attack": KEY_J, "jump": KEY_K, "dash": KEY_L, "ranged": KEY_U, "special": KEY_I, "summon": KEY_O},
		"p2": {"up": KEY_UP, "down": KEY_DOWN, "left": KEY_LEFT, "right": KEY_RIGHT,
			"attack": KEY_KP_1, "jump": KEY_KP_2, "dash": KEY_KP_3, "ranged": KEY_KP_4, "special": KEY_KP_5, "summon": KEY_KP_6}}
	var held := {}
	for item in fixture.inputs:
		if tick >= int(item.start) and tick < int(item.end):
			for key in item["keys"]: held[bindings[item.slot][key]] = true
	for slot in bindings.values():
		for key in slot.values():
			var event := InputEventKey.new()
			event.keycode = key
			event.physical_keycode = key
			event.pressed = held.has(key)
			Input.parse_input_event(event)
	Input.flush_buffered_events()
