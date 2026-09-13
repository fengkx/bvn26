extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func write_row(file: FileAccess, tick_name: String, game: Node) -> void:
	var h: HelperRuntime = game.naruto_helper
	file.store_line(JSON.stringify({
		"event": tick_name,
		"fight_tick": game.physics_tick,
		"p1": {"frame": game.naruto.current_source_frame(), "action": game.naruto.action, "x": game.naruto.source_x, "y": game.naruto.source_y, "facing": game.naruto.facing, "energy": game.naruto.energy},
		"p2": {"frame": game.ichigo.current_source_frame(), "action": game.ichigo.action, "x": game.ichigo.source_x, "y": game.ichigo.source_y, "facing": game.ichigo.facing, "hp": game.ichigo.health, "hits": game.ichigo.hits, "beida": game.ichigo.beida, "hited": game.ichigo.hited, "sw": game.ichigo.sw},
		"helper": {"id": h.helper_id, "frame": h.current_source_frame(), "x": h.position.x, "y": h.position.y, "xscale": h.scale.x, "attacking": h.attacking, "source_action": h.source_action, "visible": h.visible}
	}))

func _run() -> void:
	var out := FileAccess.open("/private/tmp/you-helper-distance200-postfix.jsonl", FileAccess.WRITE)
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	await process_frame
	game.set_physics_process(false)
	game.session.store_path = "/private/tmp/kakashi-you-vscom-local.cfg"
	game._replace_selected_actors(["卡卡西", "佐助"], ["鼬", "魂"])
	game._load_selected_stage("现世")
	game._enter_current_fight(2)
	# Keep mode 2's real receiver/game services but route P2 through its normal player path with no keys.
	game._stop_combat_drivers()
	game.session.p2cpu = false
	game._start_combat_drivers()
	game.battle_intro.cancel()
	game.naruto.root_zhanting = false
	game.ichigo.root_zhanting = false
	game.naruto.start_action("站立")
	game.ichigo.start_action("站立")
	game.naruto.source_x = 300.0
	game.naruto.source_y = 0.0
	game.naruto.sync_body_collision_position()
	game.ichigo.source_x = 480.0
	game.ichigo.source_y = 0.0
	game.ichigo.sync_body_collision_position()
	game.naruto.set_facing(1)
	game.ichigo.set_facing(-1)
	game.naruto.energy = 300.0
	write_row(out, "controlled_setup", game)
	for _i in 10:
		game._advance_fight()
	write_row(out, "before_o", game)
	var key := InputEventKey.new()
	key.keycode = KEY_O
	key.physical_keycode = KEY_O
	key.pressed = true
	Input.parse_input_event(key)
	Input.flush_buffered_events()
	for _i in 3:
		game._advance_fight()
		write_row(out, "o_held", game)
	var release := InputEventKey.new()
	release.keycode = KEY_O
	release.physical_keycode = KEY_O
	release.pressed = false
	Input.parse_input_event(release)
	Input.flush_buffered_events()
	for i in 180:
		game._advance_fight()
		var h: HelperRuntime = game.naruto_helper
		if h.current_source_frame() <= 60 or game.ichigo.hits > 0 or i % 10 == 0:
			write_row(out, "settle", game)
	out.close()
	game.queue_free()
	await process_frame
	await create_timer(0.05).timeout
	print("KAKASHI_YOU_VSCOM_LOCAL_DONE")
	quit()
