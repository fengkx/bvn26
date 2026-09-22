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
var intro_rows: Array[Dictionary] = []
var intro_player_rows: Array[Dictionary] = []
var intro_stop_rows: Array[Dictionary] = []
var audio_lifetime_rows: Array[Dictionary] = []
var wall_probe_start_ms := -1
var probe_start_ms := -1
var known_intro_players: Dictionary = {}
var source_frame_events: Array[Dictionary] = []

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	probe_start_ms = Time.get_ticks_msec()
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
	game.character_selection.available.fighters["白哉"] = "byakuya"
	game._on_characters_confirmed(["白哉", "一护"], ["魂", "魂"])
	game._on_map_confirmed("现世")
	game.naruto.source_frame_changed.connect(_on_source_frame_changed.bind("p1"))
	game.ichigo.source_frame_changed.connect(_on_source_frame_changed.bind("p2"))
	game.naruto.nested_source_sound_started.connect(_on_sound.bind("p1"))
	game.ichigo.nested_source_sound_started.connect(_on_sound.bind("p2"))
	game.diagnostic_input_provider = Callable(self, "_input_tape")
	var intro_iteration := 0
	while game.battle_intro.active:
		var before := _intro_snapshot(intro_iteration, "before")
		intro_rows.append(before)
		game._advance_fight()
		_scan_audio_players(game.naruto, "p1")
		_scan_audio_players(game.ichigo, "p2")
		_intro_scan_audio_players()
		intro_rows.append({"iteration": intro_iteration, "phase": "after", "physics_tick": game.physics_tick, "snapshot": _intro_snapshot(intro_iteration, "after")})
		intro_iteration += 1
		assert(intro_iteration <= 900, "intro did not finish")
	assert(not game.battle_intro.active, "intro did not finish")
	fight_start_tick = game.physics_tick
	_apply_setup(game.naruto, fixture.get("setup", {}).get("p1", {}))
	_apply_setup(game.ichigo, fixture.get("setup", {}).get("p2", {}))
	for _tick in int(fixture.get("frames", 300)):
		game._advance_fight()
		_observe()
	await _observe_audio_lifetime(2000)
	var source_timeline: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/byakuya/timeline.json"))
	var expected := []
	for frame in source_timeline.get("frames", []):
		for event in frame.get("events", []):
			if str(event.get("type", "")) != "start_sound":
				continue
			expected.append({"source_frame": int(frame.get("frame", 0)), "sound_id": int(event.get("sound_id", -1))})
	var result := {"format": "byakuya-audio-walk-v6", "fixture": args[0], "fixture_sha256": FileAccess.get_sha256(args[0]), "fight_start_tick": fight_start_tick, "intro_rows": intro_rows, "intro_player_created": intro_player_rows, "intro_player_finished": intro_stop_rows, "audio_lifetime_rows": audio_lifetime_rows, "source_frame_events": source_frame_events, "sound_started": sound_rows, "player_created": player_rows, "player_stopped": stop_rows, "states": state_rows, "source_reachable_sound_events": expected, "scope": "Godot main-scene action walk with same fixture input tape; intro_rows records IntroCoordinator presentation and actor-local frames before/after each natural advance; source_frame_events records the actual queue/entry signal phase, including transient frame 958; source sound tags are correlated by observed root frame, not inferred continuous sprite-frame gaps; audio lifetime uses wall-clock process frames after the bounded walk and never forces stop.", "limitations": ["native trace exposes no StartSound callback stream; Flash source side is action/frame plus timeline tags", "a player that remains active beyond the bounded fixture is reported as active, not falsely marked stopped", "device waveform equivalence is not asserted"]}
	FileAccess.open(output.path_join("audio-walk.json"), FileAccess.WRITE).store_string(JSON.stringify(result, "  ") + "\n")
	print("BYAKUYA_AUDIO_WALK_OK sounds=%d players=%d stopped=%d states=%d" % [sound_rows.size(), player_rows.size(), stop_rows.size(), state_rows.size()])
	game.queue_free()
	await process_frame
	quit()

func _apply_setup(actor: Node, setup: Dictionary) -> void:
	actor.source_x = float(setup.get("x", actor.source_x))
	actor.source_y = float(setup.get("y", actor.source_y))
	actor.energy = float(setup.get("energy", actor.energy))
	if setup.has("health"):
		actor.health = float(setup.get("health"))
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

func _intro_snapshot(iteration: int, phase: String) -> Dictionary:
	var clips := {}
	for name in game.battle_intro.clips:
		var clip: Node = game.battle_intro.clips[name]
		clips[str(name)] = {"source_frame": clip.current_source_frame(), "playing": bool(game.battle_intro.playing.get(name, false))}
	return {"iteration": iteration, "phase": phase, "physics_tick": game.physics_tick, "presentation_tick": game.physics_tick, "intro_step": game.battle_intro.step, "polling": game.battle_intro.polling, "active": game.battle_intro.active, "p1_source_frame": game.naruto.current_source_frame(), "p2_source_frame": game.ichigo.current_source_frame(), "clips": clips}

func _on_source_frame_changed(frame: int, slot: String) -> void:
	if not game.battle_intro.active and fight_start_tick >= 0:
		return
	source_frame_events.append({"slot": slot, "source_frame": frame, "physics_tick": game.physics_tick, "presentation_tick": game.physics_tick, "intro_step": game.battle_intro.step, "intro_active": game.battle_intro.active, "phase": "source_frame_changed"})

func _intro_scan_audio_players() -> void:
	for name in game.battle_intro.clips:
		var clip: Node = game.battle_intro.clips[name]
		var layer: Node = clip.get_node_or_null("SoundLayer")
		if layer == null:
			continue
		for child in layer.get_children():
			if not child is AudioStreamPlayer:
				continue
			var key := str(child.get_instance_id())
			if known_intro_players.has(key):
				continue
			known_intro_players[key] = true
			intro_player_rows.append({"player_id": key, "clip": str(name), "presentation_tick": game.physics_tick, "intro_step": game.battle_intro.step, "source_frame": clip.current_source_frame(), "stream_path": str(child.stream.resource_path) if child.stream != null else "", "playing": child.playing})
			child.finished.connect(_on_intro_player_finished.bind(key, name, str(child.stream.resource_path) if child.stream != null else ""))

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
		var created_ms := Time.get_ticks_msec()
		var row := {"player_id": key, "slot": slot, "created_fight_tick": game.physics_tick - fight_start_tick if fight_start_tick >= 0 else null, "presentation_tick": game.physics_tick, "intro_active": game.battle_intro.active, "intro_step": game.battle_intro.step, "created_source_frame": actor.current_source_frame(), "stream_path": stream_path, "playing": child.playing, "created_wall_clock_ms": created_ms, "created_wall_elapsed_ms": created_ms - probe_start_ms}
		player_rows.append(row)
		child.finished.connect(_on_player_finished.bind(key, slot, stream_path))

func _on_player_finished(key: String, slot: String, stream_path: String) -> void:
	var now_ms := Time.get_ticks_msec()
	var created_ms: Variant = null
	for row in player_rows:
		if str(row.get("player_id", "")) == key:
			created_ms = row.get("created_wall_clock_ms")
			break
	stop_rows.append({"player_id": key, "slot": slot, "stopped_fight_tick": game.physics_tick - fight_start_tick, "stopped_source_frame": game.naruto.current_source_frame(), "stream_path": stream_path, "wall_clock_ms": now_ms, "wall_elapsed_ms": now_ms - wall_probe_start_ms if wall_probe_start_ms >= 0 else null, "wall_since_player_created_ms": now_ms - int(created_ms) if created_ms != null else null})

func _on_intro_player_finished(key: String, clip_name: String, stream_path: String) -> void:
	intro_stop_rows.append({"player_id": key, "clip": clip_name, "presentation_tick": game.physics_tick, "intro_step": game.battle_intro.step, "stream_path": stream_path})

func _observe_audio_lifetime(duration_ms: int) -> void:
	wall_probe_start_ms = Time.get_ticks_msec()
	var start_ms := wall_probe_start_ms
	while Time.get_ticks_msec() - start_ms < duration_ms:
		var elapsed_ms := Time.get_ticks_msec() - start_ms
		for child: Node in game.naruto._sound_layer().get_children():
			if child is AudioStreamPlayer and child.stream != null and str(child.stream.resource_path).ends_with("/619.mp3"):
				audio_lifetime_rows.append({"elapsed_ms": elapsed_ms, "player_id": str(child.get_instance_id()), "exists": true, "playing": child.playing, "playback_position": child.get_playback_position(), "wall_clock_ms": Time.get_ticks_msec()})
		await process_frame
		await process_frame
