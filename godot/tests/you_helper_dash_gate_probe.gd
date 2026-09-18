extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame
	game._goto_character_selection(3)
	game._on_characters_confirmed(["佐助", "恋次"], ["鼬", "魂"])
	game._on_map_confirmed("现世")
	for _tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	assert(not game.battle_intro.active)
	game.naruto.energy = 300.0
	game.ichigo.energy = 300.0
	game.naruto.position.x = 300.0
	game.ichigo.position.x = 350.0
	var rows: Array = []
	game.diagnostic_input_provider = func(slot: String, _physics_tick: int) -> Dictionary:
		var helper_frame: int = game.naruto_helper.current_source_frame()
		if slot == "p1":
			# The inactive helper remains on source frame 1 until the first
			# accepted summon.  This keeps the tape independent of intro length.
			return {"summon": helper_frame == 1}
		# Drive each window from the helper's source frame, not an assumed
		# fight tick.  The provider is called before helper.advance_timeline().
		return {"dash": (helper_frame >= 8 and helper_frame <= 10)
			or (helper_frame >= 23 and helper_frame <= 26)
			or (helper_frame >= 65 and helper_frame <= 67)}
	for tick in 140:
		game._advance_fight([], func() -> bool:
			rows.append({
				"tick": tick,
				"helper_frame": game.naruto_helper.current_source_frame(),
				"helper_action": game.naruto_helper.source_action,
				"root_zhanting": game.naruto.root_zhanting,
				"defender_action": game.ichigo.action,
				"defender_frame": game.ichigo.current_source_frame(),
				"defender_x": game.ichigo.position.x,
				"defender_health": game.ichigo.health,
				"defender_hits": game.ichigo.hits,
				"defender_hited": game.ichigo.hited,
				"defender_timeline_playing": game.ichigo.timeline_playing,
				"defender_energy": game.ichigo.energy,
			})
			return false
			)
	var output := OS.get_cmdline_user_args()[0] if not OS.get_cmdline_user_args().is_empty() else ""
	if output != "":
		FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(rows, "\t") + "\n")
	print("YOU_HELPER_DASH_GATE_PROBE_OK rows=", rows.size())
	game.queue_free()
	await process_frame
	quit()
