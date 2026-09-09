extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	var helper_id := args[1] if args.size() > 1 else "woailuo"
	var mode := int(args[2]) if args.size() > 2 else 2
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	if helper_id == "kon":
		game.naruto_helper.free()
		game.naruto_helper = game._make_helper("res://generated/helpers/kon")
	game._enter_current_fight(mode)
	if game.cpu_driver != null:
		game.ichigo.ai_random_clock.cancel()
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active)
	for key in ["goran", "attran", "defran", "jumpran", "bisharan"]:
		game.ichigo.ai_source_state.values[key] = 400
	game.ichigo.ai_source_state.values["bisharan"] = NAN
	game.naruto.position.x = 300
	game.ichigo.position.x = 340 if helper_id == "kon" else 420
	game.naruto.energy = 100
	game.ichigo.energy = 200 if helper_id == "kon" else 0
	var rows := []
	for tick in 180:
		if tick == 10 or tick == 15:
			var key := InputEventKey.new()
			key.keycode = KEY_O
			key.physical_keycode = KEY_O
			key.pressed = tick == 10
			Input.parse_input_event(key)
			Input.flush_buffered_events()
		var root_state := {}
		game._advance_fight([], func() -> bool:
			root_state["frame"] = game.ichigo.current_source_frame()
			root_state["hits"] = game.ichigo.hits
			return false
		)
		rows.append({"tick": tick, "helper_frame": game.naruto_helper.current_source_frame(),
			"child_frame": _child_frame(game.naruto_helper),
			"helper_active": game.naruto_helper.attacking,
			"sand": game.naruto_helper.instance_global_bounds("atm1").has_area(),
			"defender_frame": game.ichigo.current_source_frame(), "hp": game.ichigo.health,
			"hits": game.ichigo.hits, "pause": game.ichigo.root_zhanting,
			"energy": game.ichigo.energy, "root_state": root_state})
	if not args.is_empty():
		FileAccess.open(args[0], FileAccess.WRITE).store_string(JSON.stringify(rows, "\t") + "\n")
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("HELPER_DURATION_REFERENCE_OK")
	quit()


func _child_frame(helper: HelperRuntime) -> Variant:
	for placement: Dictionary in helper._frames[helper.current_source_frame()]["display_list"]:
		if placement.get("name", "") == "atm1":
			var definition: Dictionary = helper._definitions[int(placement["character_id"])]
			return helper._nested_frame(placement, helper.current_source_frame(), int(definition["frame_count"]))
	return null
