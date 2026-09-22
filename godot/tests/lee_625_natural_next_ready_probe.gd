extends SceneTree

## Analysis-only probe: keep SceneTree Timer realtime and observe the natural
## KO -> nextfight -> Ready path. It never emits timeout or writes expected
## state fields; the fixture only supplies the same input/preconditions.
var game: Node
var fixture: Dictionary
var fixture_inputs: Array = []
var fight_start_tick := -1
var rows: Array[Dictionary] = []
var timer_rows: Array[Dictionary] = []
var timer_seen: Dictionary = {}
var probe_start_ms := 0
var finished := false
var post_ready_tick := -1

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2, "Expected fixture and output directory")
	fixture = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	fixture_inputs = fixture.get("inputs", [])
	probe_start_ms = Time.get_ticks_msec()
	var output := str(args[1])
	DirAccess.make_dir_recursive_absolute(output)
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.recorded_training_timers = true
	game.character_selection.available.fighters["小李"] = "lee"
	game._replace_selected_actors(["小李", "一护"], ["我爱罗", "魂"])
	game._load_selected_stage("现世")
	game._enter_current_fight(3)
	while game.battle_intro.active:
		game._advance_fight()
		await process_frame
	assert(not game.battle_intro.active, "intro did not finish")
	fight_start_tick = game.physics_tick
	_apply_setup(game.naruto, fixture.get("setup", {}).get("p1", {}))
	_apply_setup(game.ichigo, fixture.get("setup", {}).get("p2", {}))
	_apply_source_state_preconditions(game.naruto)
	_apply_source_state_preconditions(game.ichigo)
	game.diagnostic_input_provider = Callable(self, "_input_tape")
	for tick in 901:
		var before_p1 := _actor_state(game.naruto)
		var before_p2 := _actor_state(game.ichigo)
		var input_before := {"p1": _input_tape("p1", game.physics_tick), "p2": _input_tape("p2", game.physics_tick)}
		game._advance_fight([], Callable(self, "_observe"))
		await process_frame
		await process_frame
		if rows.size() > 4 and post_ready_tick < 0 and _saw_next_ready():
			post_ready_tick = 0
		if post_ready_tick >= 0:
			var after := rows[rows.size() - 1]
			after["post_ready_input_before"] = input_before
			after["post_ready_state_before"] = {"p1": before_p1, "p2": before_p2}
			after["post_ready_input_after"] = {"p1": _input_tape("p1", game.physics_tick), "p2": _input_tape("p2", game.physics_tick)}
			after["post_ready_state_after"] = {"p1": after.get("p1", {}), "p2": after.get("p2", {})}
			post_ready_tick += 1
		if post_ready_tick > 12:
			break
	var result := {
		"format": "lee-625-natural-next-ready-v1",
		"fixture": args[0],
		"fixture_sha256": FileAccess.get_sha256(args[0]),
		"probe_start_wall_clock_ms": probe_start_ms,
		"runtime_physics_hz": Engine.physics_ticks_per_second,
		"rows": rows,
		"timer_rows": timer_rows,
		"scope": "Natural SceneTree Timer and _ko_nextfight timeout route; no timeout.emit, no source-tape timer delivery, no virtual physics clock",
		"limitations": ["Godot native lifecycle only; source Flash lifecycle must be captured separately", "wall-clock timestamps are diagnostic and are not asserted equal to Flash"]
	}
	FileAccess.open(output.path_join("natural-next-ready.json"), FileAccess.WRITE).store_string(JSON.stringify(result, "  ") + "\n")
	print("LEE_625_NATURAL_NEXT_READY_OK rows=%d timers=%d elapsed_ms=%d" % [rows.size(), timer_rows.size(), Time.get_ticks_msec() - probe_start_ms])
	game.queue_free()
	await process_frame
	quit(0 if _saw_next_ready() else 1)

func _apply_setup(actor: Node, setup: Dictionary) -> void:
	actor.source_x = float(setup.get("x", actor.source_x))
	actor.source_y = float(setup.get("y", actor.source_y))
	actor.energy = float(setup.get("energy", actor.energy))

func _apply_source_state_preconditions(actor: Node) -> void:
	var values: Dictionary = fixture.get("source_state_preconditions", {}).get(str(actor.player_slot), {})
	for field in values:
		if field == "health":
			actor.health = float(values[field])
		else:
			actor.ai_source_state.apply_write({"field": str(field), "value": values[field]})
		actor.sync_body_collision_position()

func _input_tape(slot: String, tick: int) -> Dictionary:
	var keys := {"up": false, "down": false, "left": false, "right": false, "attack": false, "jump": false, "dash": false, "ranged": false, "special": false, "summon": false}
	if post_ready_tick >= 0 and slot == "p1":
		# Exercise the normal input path after Ready; this probe never writes action or position.
		if post_ready_tick < 4:
			keys["right"] = true
		elif post_ready_tick < 8:
			keys["attack"] = true
		return keys
	var relative := tick - fight_start_tick
	for item in fixture_inputs:
		if str(item.get("slot", "")) == slot and relative >= int(item.get("start", 0)) and relative < int(item.get("end", 0)):
			for key in item.get("keys", []):
				keys[str(key)] = true
	return keys

func _observe() -> bool:
	var now := Time.get_ticks_msec()
	var row := {"wall_elapsed_ms": now - probe_start_ms, "physics_tick": game.physics_tick, "fight_tick": game.physics_tick - fight_start_tick, "root_label": str(game.session.root_label), "intro_active": game.battle_intro.active, "ko_active": game.ko_active, "ko_paused": game.ko_paused, "ko_terminal_pending": game.ko_terminal_pending, "ko_timer_id": _timer_id(), "ko_timer_stopped": _timer_stopped(), "p1": _actor_state(game.naruto), "p2": _actor_state(game.ichigo)}
	rows.append(row)
	_observe_timer(now)
	return false

func _actor_state(actor: Node) -> Dictionary:
	return {"slot": str(actor.player_slot), "health": actor.health, "action": actor.action, "frame": actor.current_source_frame(), "source_x": actor.source_x, "source_y": actor.source_y, "sw": actor.sw, "paused": actor.root_zhanting, "touchFloor": actor.ai_source_state.read_field("touchFloor")}

func _timer_id() -> Variant:
	return game.ko_nextfight_timer.get_instance_id() if game.ko_nextfight_timer != null else null

func _timer_stopped() -> Variant:
	return game.ko_nextfight_timer.is_stopped() if game.ko_nextfight_timer != null else null

func _observe_timer(now: int) -> void:
	if game.ko_nextfight_timer == null:
		return
	var timer: Timer = game.ko_nextfight_timer
	var id := str(timer.get_instance_id())
	if not timer_seen.has(id):
		timer_seen[id] = true
		timer.timeout.connect(_on_timer_timeout.bind(id))
		timer_rows.append({"event": "register_observed", "id": id, "wait_ms": timer.wait_time * 1000.0, "wall_elapsed_ms": now - probe_start_ms, "physics_tick": game.physics_tick, "root_label": str(game.session.root_label), "ko_active": game.ko_active})

func _on_timer_timeout(id: String) -> void:
	timer_rows.append({"event": "timeout_observed", "id": id, "wall_elapsed_ms": Time.get_ticks_msec() - probe_start_ms, "physics_tick": game.physics_tick, "root_label": str(game.session.root_label), "ko_active": game.ko_active, "p1_health": game.naruto.health, "p2_health": game.ichigo.health})

func _saw_next_ready() -> bool:
	for row in rows:
		if int(row.get("fight_tick", -1)) > 0 and not bool(row.get("intro_active", true)) and str(row.get("root_label", "")) == "游戏场景" and not bool(row.get("ko_active", true)):
			if int(row.get("physics_tick", 0)) > fight_start_tick + 200:
				return true
	return false
