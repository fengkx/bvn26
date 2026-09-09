extends SceneTree

var boundaries: Array = []


func _initialize() -> void:
	_run.call_deferred()


func _observe(frame: int, entering: bool, fighter: FighterRuntime) -> void:
	if (frame == 390 and not entering) or frame == 1:
		boundaries.append({"entering": entering, "values": [frame,
			fighter.current_source_frame(), float(fighter.ai_source_state.read_field("动作")),
			fighter.energy, fighter.sw]})


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	assert(source["transition_count"] == 1)
	var transition: Dictionary = source["transitions"][0]
	var expected: Array = []
	for key in ["caller_exit", "target_entry", "target_exit"]:
		var values := str(transition[key]["value"]).split(",")
		expected.append({"entering": key == "target_entry", "values": [int(values[0]),
			int(values[1]), float(values[2]), float(values[3]), values[4] == "true"]})
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	for tick in 600:
		game._advance_fight()
		if not game.battle_intro.active: break
	assert(not game.battle_intro.active)
	var fighter: FighterRuntime = game.ichigo
	fighter.source_frame_script_boundary.connect(_observe.bind(fighter))
	# Match the explicitly marked r06 fixture; this is not a match replay.
	fighter.play_source_frame(389)
	fighter.timeline_playing = true
	fighter._queue_source_frame(389)
	fighter.ai_source_state.values["动作"] = 1
	fighter.energy = 0
	fighter.root_zhanting = true
	game.naruto.root_zhanting = true
	game._advance_fight()
	var matches := boundaries == expected
	var report := {"status": "frame_script_boundaries_match" if matches else "first_difference",
		"reference_sha256": FileAccess.get_sha256(args[0]), "expected": expected,
		"actual": boundaries, "whole_match_parity_verified": false,
		"limits": ["Controlled r06 fixture only.", "Does not assign the original root observer to a native whole-world phase."]}
	FileAccess.open(args[1], FileAccess.WRITE).store_string(JSON.stringify(report, "\t") + "\n")
	game._goto_menu()
	game.queue_free()
	await process_frame
	assert(matches)
	print("FRAME_OBSERVATION_REFERENCE_OK")
	quit()
