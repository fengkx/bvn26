extends SceneTree

var game: Node
var fixture: Dictionary
var fixture_inputs: Array = []
var fight_start_tick := -1
var sound_rows: Array[Dictionary] = []
var player_rows: Array[Dictionary] = []
var stop_rows: Array[Dictionary] = []
var known_players: Dictionary = {}
var state_rows: Array[Dictionary] = []

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2, "Expected fixture and output directory")
	fixture = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	fixture_inputs = fixture.get("inputs", [])
	var output := str(args[1])
	DirAccess.make_dir_recursive_absolute(output)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._on_menu_confirmed("vs_com")
	game.character_selection.available.fighters["小李"] = "lee"
	game._on_characters_confirmed(["小李", "一护"], ["我爱罗", "魂"])
	game._on_map_confirmed("现世")
	game.naruto.nested_source_sound_started.connect(_on_sound.bind("p1"))
	game.ichigo.nested_source_sound_started.connect(_on_sound.bind("p2"))
	game.diagnostic_input_provider = Callable(self, "_input_tape")
	for _tick in 900:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active, "intro did not finish")
	fight_start_tick = game.physics_tick
	_apply_setup(game.naruto, fixture.get("setup", {}).get("p1", {}))
	_apply_setup(game.ichigo, fixture.get("setup", {}).get("p2", {}))
	for _tick in int(fixture.get("frames", 300)):
		game._advance_fight()
		_observe()
	var source_timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/lee/timeline.json"))
	var expected := []
	for frame in source_timeline.get("frames", []):
		for event in frame.get("events", []):
			if str(event.get("type", "")) != "start_sound":
				continue
			expected.append({"source_frame": int(frame.get("frame", 0)), "sound_id": int(event.get("sound_id", -1))})
	var result := {"format": "lee-audio-walk-v2", "fixture": args[0], "fixture_sha256": FileAccess.get_sha256(args[0]), "fight_start_tick": fight_start_tick, "sound_started": sound_rows, "player_created": player_rows, "player_stopped": stop_rows, "states": state_rows, "source_reachable_sound_events": expected, "scope": "Godot main-scene action walk with same fixture input tape; source sound tags are correlated by observed root frame, not inferred continuous sprite-frame gaps.", "limitations": ["native trace exposes no StartSound callback stream; Flash source side is action/frame plus timeline tags", "a player that remains active beyond the bounded fixture is reported as active, not falsely marked stopped", "device waveform equivalence is not asserted"]}
	FileAccess.open(output.path_join("audio-walk.json"), FileAccess.WRITE).store_string(JSON.stringify(result, "  ") + "\n")
	print("LEE_AUDIO_WALK_OK sounds=%d players=%d stopped=%d states=%d" % [sound_rows.size(), player_rows.size(), stop_rows.size(), state_rows.size()])
	game.queue_free()
	await process_frame
	quit()

func _apply_setup(actor: Node, setup: Dictionary) -> void:
	actor.source_x = float(setup.get("x", actor.source_x))
	actor.source_y = float(setup.get("y", actor.source_y))
	actor.energy = float(setup.get("energy", actor.energy))
	actor.sync_body_collision_position()

func _input_tape(slot: String, tick: int) -> Dictionary:
	var keys := {"up": false, "down": false, "left": false, "right": false, "attack": false, "jump": false, "dash": false, "ranged": false, "special": false, "summon": false}
	if fight_start_tick < 0:
		return keys
	var relative := tick - fight_start_tick
	for item in fixture_inputs:
		if str(item.get("slot", "")) != slot or relative < int(item.get("start", 0)) or relative >= int(item.get("end", 0)):
			continue
		for key in item.get("keys", []):
			keys[str(key)] = true
	return keys

func _on_sound(event: Dictionary, slot: String) -> void:
	var row := event.duplicate(true)
	row["slot"] = slot
	row["physics_tick"] = game.physics_tick
	row["fight_tick"] = game.physics_tick - fight_start_tick
	sound_rows.append(row)

func _observe() -> void:
	_scan_audio_players(game.naruto, "p1")
	_scan_audio_players(game.ichigo, "p2")
	state_rows.append({"fight_tick": game.physics_tick - fight_start_tick, "source_frame": game.naruto.current_source_frame(), "action": game.naruto.action, "energy": game.naruto.energy, "root_sound_ids": game.naruto.last_sound_ids.duplicate(), "nested_sound_ids": game.naruto.last_nested_sound_ids.duplicate()})

func _scan_audio_players(actor: Node, slot: String) -> void:
	var layer: Node = actor._sound_layer()
	for child in layer.get_children():
		if not child is AudioStreamPlayer:
			continue
		var key := str(child.get_instance_id())
		if known_players.has(key):
			continue
		known_players[key] = true
		var stream_path := str(child.stream.resource_path) if child.stream != null else ""
		var row := {"player_id": key, "slot": slot, "created_fight_tick": game.physics_tick - fight_start_tick, "created_source_frame": actor.current_source_frame(), "stream_path": stream_path, "playing": child.playing}
		player_rows.append(row)
		child.finished.connect(_on_player_finished.bind(key, slot, stream_path))

func _on_player_finished(key: String, slot: String, stream_path: String) -> void:
	stop_rows.append({"player_id": key, "slot": slot, "stopped_fight_tick": game.physics_tick - fight_start_tick, "stopped_source_frame": game.naruto.current_source_frame(), "stream_path": stream_path})
