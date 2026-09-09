extends SceneTree

var game
var scenario: String
var dash_start := -1
var rows: Array = []
var trigger_frame := -1
var dash_duration := 36


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() >= 2)
	if args.size() > 2:
		trigger_frame = int(args[2])
	if args.size() > 3:
		dash_duration = int(args[3])
	scenario = args[0]
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active)
	for tick in 241:
		game._advance_fight([], func() -> bool:
			_observe(tick)
			return false
		)
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(rows, "\t") + "\n")
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("DASH_REFERENCE_OK")
	quit()


func _observe(tick: int) -> void:
	var a: FighterRuntime = game.naruto
	var b: FighterRuntime = game.ichigo
	var h: HelperRuntime = game.naruto_helper
	if tick == 0:
		a.goto_ai_label("站立", true)
		b.goto_ai_label("站立", true)
		a.position.x = 300
		a.set_facing(-1)
		b.position.x = 600
		b.set_facing(-1)
		a.energy = 300
		b.energy = 300
		for key in ["goran", "attran", "defran", "jumpran"]:
			b.ai_source_state.values[key] = 400
		b.ai_source_state.values["bisharan"] = NAN
	if dash_start < 0 and ((scenario.begins_with("helper") and h.current_source_frame() == (trigger_frame if trigger_frame >= 0 else (8 if scenario.ends_with("rush") else 50))) or
		(scenario.begins_with("super") and a.current_source_frame() == (trigger_frame if trigger_frame >= 0 else 610))):
		dash_start = tick
	var elapsed := tick - dash_start
	if dash_start >= 0:
		if scenario.ends_with("dashx"):
			if elapsed in [0, 12]:
				b.goto_ai_label("砍1", true)
			b.ai_source_state.values["goran"] = 130 if elapsed < 24 else 400
		else:
			b.ai_source_state.values["goran"] = 150 if elapsed < dash_duration else 400
	var bounds := h.instance_global_bounds("atm1")
	if bounds.has_area():
		bounds = h._transform_rect(game.game_world.global_transform.affine_inverse(), bounds)
	rows.append({"tick": tick, "attacker_frame": a.current_source_frame(),
		"defender_frame": b.current_source_frame(), "hp": b.health, "hits": b.hits,
		"canhit": b.ai_source_state.read_field("canhit"), "dashing": b.ai_source_state.read_field("dashing"),
		"dash_frame": b.ai_source_state.read_field("dashF"), "energy": b.energy,
		"x": b.position.x, "paused": b.root_zhanting, "helper_frame": h.current_source_frame(),
		"helper_child": h.instance_clip_frame("atm1"), "sand": bounds.has_area(),
		"sand_min": bounds.position.x, "sand_max": bounds.end.x,
		"clone_frame": a.instance_clip_frame("fensheng"),
		"receiver": b.instance_clip_frame("bdmn"), "dash_start": dash_start,
		"y": b.position.y, "body_bounds": str(b.instance_global_bounds("bdmn")),
		"attack_bounds": str(a.source_projectile_target_bounds("sbsatm"))})
	for key in [KEY_O, KEY_W, KEY_I]:
		var event := InputEventKey.new()
		event.keycode = key
		event.physical_keycode = key
		event.pressed = tick >= 10 and tick < 15 and (
			(key == KEY_O) == scenario.begins_with("helper"))
		Input.parse_input_event(event)
	Input.flush_buffered_events()
