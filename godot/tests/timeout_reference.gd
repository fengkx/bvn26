extends SceneTree
var game
var rows: Array = []
var draw := false
func _initialize() -> void:
	_run.call_deferred()
func observe(tick: int) -> bool:
	if tick == 0:
		game.ichigo.ai_random_clock.cancel()
		for field in ["goran", "attran", "defran", "jumpran"]: game.ichigo.ai_source_state.values[field] = 500
		game.ichigo.ai_source_state.values["bisharan"] = NAN
		game.naruto.health = 800
		game.ichigo.health = 800 if draw else 600
		game.session.maxtime = 30
		game.ko_state["_root.gametime"] = 1
		game.countdown.fire()
	rows.append([game.timeout_timeline.root_clip.frame,game.ko_state["_root.gametime"],game.ko_state["_root.to"],game.ko_state["_root.p1ws"],game.ko_state["_root.p2ws"],game.naruto.sw,game.ichigo.sw,game.naruto.root_zhanting,game.ko_state["_root.rounds"]])
	return false
func _run() -> void:
	var args := OS.get_cmdline_user_args()
	draw = args[0] == "draw"
	game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game.ko_recorded_timers = true
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active: break
	assert(not game.battle_intro.active)
	for tick in 360:
		game._advance_fight([], func() -> bool: return observe(tick))
	var source_path := "res://../evidence/config/timeout-%s/events.jsonl" % ("draw" if draw else "p1")
	var expected: Array = []
	for line in FileAccess.get_file_as_string(source_path).split("\n", false):
		var event: Dictionary = JSON.parse_string(line)
		if event.kind != "timeout_state": continue
		var row: Array = []
		for field in str(event.value).split(","):
			row.append(JSON.parse_string(field) if field in ["true", "false"] else int(field))
		expected.append(row)
	var compared := 0
	for tick in mini(rows.size(), expected.size()):
		# The separate wall-clock nextfight is disabled in this deterministic
		# playback. Compare the entire authored sequence before its first call.
		if int(expected[tick][8]) != 1: break
		for field in expected[tick].size():
			var same: bool = rows[tick][field] == expected[tick][field] if field in [2, 5, 6, 7] else float(rows[tick][field]) == float(expected[tick][field])
			assert(same, "Timeout source difference at %d field %d: %s != %s" % [tick, field, rows[tick], expected[tick]])
		compared += 1
	assert(compared > 200)
	assert(game.ko_nextfight_timer != null)
	game._ko_nextfight()
	assert(game.ko_state["_root.rounds"] == 2 and not game.naruto.sw and not game.ichigo.sw)
	assert(game.naruto.health == game.session.maxhp and game.ichigo.health == game.session.maxhp)
	assert(game.ko_state["_root.gametime"] == 30)
	FileAccess.open(args[1],FileAccess.WRITE).store_string(JSON.stringify({"compared_snapshots": compared, "rows": rows}))
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("TIMEOUT_REFERENCE_OK")
	quit()
