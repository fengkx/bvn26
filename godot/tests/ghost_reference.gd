extends SceneTree

var game
var scenario: String
var rows: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() >= 2)
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
	for tick in 81:
		game._advance_fight([], func() -> bool:
			_observe(tick)
			return false
		)
		if args.size() > 2 and tick == 15:
			await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(args[2])
	var expected: Array = []
	var path := "res://../evidence/combat/ghost-validation/%s/events.jsonl" % scenario
	for line in FileAccess.get_file_as_string(path).split("\n", false):
		var event: Dictionary = JSON.parse_string(line)
		if event.kind != "ghost_state": continue
		var row: Array = []
		for field in str(event.value).split(","):
			row.append(null if field == "undefined" else JSON.parse_string(field))
		expected.append(row)
	assert(expected.size() == rows.size())
	for tick in rows.size():
		for field in rows[tick].size():
			var original: Variant = expected[tick][field]
			var native: Variant = rows[tick][field]
			if field == 10 and original == null: original = 0
			assert(native == original, "Ghost mismatch at %d field %d: %s != %s" % [tick, field, native, original])
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(rows, "\t") + "\n")
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("GHOST_REFERENCE_OK")
	quit()


func _observe(tick: int) -> void:
	var a: FighterRuntime = game.naruto
	var b: FighterRuntime = game.ichigo
	if tick == 0:
		a.goto_ai_label("站立", true)
		b.goto_ai_label("站立", true)
		a.position.x = 300
		b.position.x = 600
		a.energy = 99 if scenario == "low" else 300
		for key in ["goran", "attran", "defran", "jumpran"]:
			b.ai_source_state.values[key] = 400
		b.ai_source_state.values["bisharan"] = NAN
	if tick == 10:
		if scenario == "hurt":
			for key in ["htx", "yup", "time", "hstm"]:
				a.ai_source_state.values[key] = 0
			a.ai_source_state.values["tdtime"] = 30
			a.hited = 1
			a.goto_ai_label("被打", false)
		else:
			a.goto_ai_label("砍1", true)
	if tick == 14 and scenario in ["down", "up"]:
		var found := false
		for child in game.game_world.get_children():
			if child is HitEffectRuntime and child._directory.ends_with("/XG_xdash"):
				found = true
		assert(found, "Source ghost effect must be materialized and spawned")
	var state := a.ai_source_state
	rows.append([a.current_source_frame(), state.read_field("动作"), a.energy,
		state.read_field("dashing"), state.read_field("dashF"), a.position.x,
		a.position.y, a.root_zhanting, a.bs, state.read_field("canhit"), a.instance_clip_frame("bdmn")])
	for key in [KEY_S, KEY_W, KEY_L]:
		var event := InputEventKey.new()
		event.keycode = key
		event.physical_keycode = key
		event.pressed = ((tick >= 12 and tick < 15) or (tick >= 27 and tick < 30)) and (key == KEY_L or (key == KEY_W if scenario == "up" else key == KEY_S))
		Input.parse_input_event(event)
	Input.flush_buffered_events()
