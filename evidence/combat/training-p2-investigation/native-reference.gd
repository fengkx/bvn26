extends SceneTree

var game
var mode: int
var rows: Array = []
var recovery_events: Dictionary = {}

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var args := OS.get_cmdline_user_args()
	mode = int(args[0])
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.recorded_training_timers = true
	if args.size() > 2:
		for line in FileAccess.get_file_as_string(args[2]).split("\n", false):
			var event: Dictionary = JSON.parse_string(line)
			if event.kind != "training_recovery" or int(event.fight_tick) < 0: continue
			var tick := int(event.fight_tick) + 1
			if not recovery_events.has(tick): recovery_events[tick] = []
			recovery_events[tick].append({"kind": "training_recovery", "phase": "after_actor_advance"})
	if true:
		game.character_selection.available.fighters["日番谷"] = "rifagu"
		game._replace_selected_actors(["鸣人", "鼬"], ["我爱罗", "魂"])
	game._enter_current_fight(mode)
	for tick in 700:
		game._advance_fight([], func() -> bool:
			if not game.battle_intro.active: _observe(0)
			return false)
		if not game.battle_intro.active: break
	assert(not game.battle_intro.active and rows.size() == 2)
	for tick in range(1, 301):
		game._advance_fight(recovery_events.get(tick, []), func() -> bool:
			_observe(tick)
			return false)
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(rows))
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("MODE_COMBAT_REFERENCE_OK")
	quit()

func _observe(tick: int) -> void:
	if tick == 0:
		game.naruto.goto_ai_label("站立", true)
		game.ichigo.goto_ai_label("站立", true)
		game.naruto.position.x = 300
		game.ichigo.position.x = 550
		game.naruto.energy = 300
		game.ichigo.energy = 300
	for actor in [game.naruto, game.ichigo]:
		rows.append({"tick": tick, "slot": actor.player_slot, "frame": actor.current_source_frame(),
			"x": actor.source_x, "y": actor.source_y, "xscale": actor.scale.x * 100,
			"action": actor.ai_source_state.read_field("动作"), "hp": actor.health,
			"ql": actor.energy, "sw": actor.sw, "touch": actor.ai_source_state.read_field("touch"),
			"touchFloor": actor.ai_source_state.read_field("touchFloor"), "hits": actor.hits,
			"paused": actor.root_zhanting, "hstm": actor.ai_source_state.read_field("hstm"),
			"hurtSkling": actor.ai_source_state.read_field("hurtSkling")})
	var held := {}
	if tick >= 5 and tick < 17: held.merge({KEY_D: true, KEY_LEFT: true})
	if tick >= 22 and tick < 26: held.merge({KEY_J: true, KEY_KP_1: true})
	if (tick >= 60 and tick < 63) or (tick >= 80 and tick < 83):
		held.merge({KEY_W: true, KEY_L: true, KEY_DOWN: true, KEY_KP_3: true})
	if tick >= 110 and tick < 115: held.merge({KEY_W: true, KEY_I: true, KEY_KP_3: true})
	if tick >= 180 and tick < 185: held.merge({KEY_O: true, KEY_KP_6: true})
	for key in [KEY_D, KEY_LEFT, KEY_J, KEY_KP_1, KEY_W, KEY_L, KEY_DOWN, KEY_KP_3, KEY_I, KEY_O, KEY_KP_6]:
		var event := InputEventKey.new()
		event.keycode = key
		event.physical_keycode = key
		event.pressed = held.has(key)
		Input.parse_input_event(event)
	Input.flush_buffered_events()
