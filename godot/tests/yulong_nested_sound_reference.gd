extends SceneTree

var game
var fixture: Dictionary
var state_rows: Array[Dictionary] = []
var sound_rows: Array[Dictionary] = []
var playhead_rows: Array[Dictionary] = []
var current_tick := 0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2, "Expected fixture JSON and output directory")
	var fixture_path := args[0]
	var output_directory := args[1]
	fixture = JSON.parse_string(FileAccess.get_file_as_string(fixture_path))
	DirAccess.make_dir_recursive_absolute(output_directory)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.recorded_training_timers = true
	var display_id := _fixture_fighter_display_id(str(fixture.fighter))
	game.character_selection.available.fighters[display_id] = str(fixture.fighter)
	game._replace_selected_actors(
		[display_id, "一护"], ["我爱罗", "魂"]
	)
	game.naruto.nested_source_sound_started.connect(_on_nested_sound_started.bind("p1"))
	game.ichigo.nested_source_sound_started.connect(_on_nested_sound_started.bind("p2"))
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	for _tick in 700:
		game._advance_fight([], func() -> bool:
			if not game.battle_intro.active:
				_observe(0)
			return false
		)
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active and state_rows.size() == 2)
	for tick in range(1, int(fixture.frames) + 1):
		current_tick = tick
		game._advance_fight([], func() -> bool:
			_observe(tick)
			return false
		)
	var state_path := output_directory.path_join("states.json")
	var sound_path := output_directory.path_join("nested-sounds.json")
	FileAccess.open(state_path, FileAccess.WRITE).store_string(JSON.stringify(state_rows, "", true, true))
	FileAccess.open(sound_path, FileAccess.WRITE).store_string(JSON.stringify(sound_rows, "  ") + "\n")
	var playhead_path := output_directory.path_join("nested-playheads.json")
	FileAccess.open(playhead_path, FileAccess.WRITE).store_string(JSON.stringify(playhead_rows, "  ") + "\n")
	print("YULONG_NESTED_SOUND_REFERENCE_OK states=%d sounds=%d" % [state_rows.size(), sound_rows.size()])
	game._goto_menu()
	game.queue_free()
	await process_frame
	quit()


func _fixture_fighter_display_id(fixture_id: String) -> String:
	var directory := "res://generated/fighters/%s" % fixture_id
	var fighter_path := directory.path_join("fighter.json")
	var timeline_path := directory.path_join("timeline.json")
	assert(FileAccess.file_exists(fighter_path) and FileAccess.file_exists(timeline_path))
	var fighter_data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(fighter_path))
	var timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(timeline_path))
	var display_id := str(fighter_data.get("fighter_id", ""))
	assert(not display_id.is_empty(), "Generated fighter has no source display id")
	assert(str(timeline.get("source_swf", {}).get("path", "")).get_file().get_basename().to_lower() == fixture_id.to_lower())
	var source_path := "res://../" + str(timeline.source_swf.path)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../manifest.json"))
	var expected_sha := str(manifest.get("file_sha256", {}).get(str(timeline.source_swf.path), ""))
	assert(not expected_sha.is_empty() and expected_sha == str(timeline.source_swf.sha256))
	assert(FileAccess.get_sha256(source_path) == expected_sha, "Fixture source hash differs from frozen source")
	return display_id


func _on_nested_sound_started(event: Dictionary, slot: String) -> void:
	var observation := event.duplicate(true)
	observation["slot"] = slot
	observation["fight_tick"] = current_tick
	sound_rows.append(observation)


func _observe(tick: int) -> void:
	if tick == 0:
		for actor in [game.naruto, game.ichigo]:
			var setup: Dictionary = fixture.setup[actor.player_slot]
			actor.goto_ai_label("站立", true)
			actor.position.x = setup.x
			actor.energy = setup.energy
	for actor in [game.naruto, game.ichigo]:
		if actor.player_slot == "p1":
			playhead_rows.append({
				"tick": tick,
				"root_frame": actor.current_source_frame(),
				"nested_frame": actor.instance_clip_frame("shijie"),
				"nested_age": actor.instance_clip_age("shijie"),
				"nested_clip": actor._instance_local_frames.get("shijie", {}).duplicate(true),
			})
		state_rows.append({
			"tick": tick,
			"slot": actor.player_slot,
			"frame": actor.current_source_frame(),
			"x": actor.source_x,
			"y": actor.source_y,
			"xscale": actor.scale.x * 100,
			"action": actor.ai_source_state.read_field("动作"),
			"hp": actor.health,
			"ql": actor.energy,
			"sw": actor.sw,
			"touch": actor.ai_source_state.read_field("touch"),
			"touchFloor": actor.ai_source_state.read_field("touchFloor"),
			"hits": actor.hits,
			"paused": actor.root_zhanting,
			"hstm": actor.ai_source_state.read_field("hstm"),
			"hurtSkling": actor.ai_source_state.read_field("hurtSkling"),
		})
	var bindings := {
		"p1": {"up": KEY_W, "down": KEY_S, "left": KEY_A, "right": KEY_D,
			"attack": KEY_J, "jump": KEY_K, "dash": KEY_L, "ranged": KEY_U, "special": KEY_I, "summon": KEY_O},
		"p2": {"up": KEY_UP, "down": KEY_DOWN, "left": KEY_LEFT, "right": KEY_RIGHT,
			"attack": KEY_KP_1, "jump": KEY_KP_2, "dash": KEY_KP_3, "ranged": KEY_KP_4, "special": KEY_KP_5, "summon": KEY_KP_6},
	}
	var held: Dictionary = {}
	for item: Dictionary in fixture.inputs:
		if tick >= int(item.start) and tick < int(item.end):
			for key: String in item.keys:
				held[bindings[item.slot][key]] = true
	for slot: Dictionary in bindings.values():
		for keycode: int in slot.values():
			var input_event := InputEventKey.new()
			input_event.keycode = keycode
			input_event.physical_keycode = keycode
			input_event.pressed = held.has(keycode)
			Input.parse_input_event(input_event)
	Input.flush_buffered_events()
