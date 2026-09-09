extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var session := GameSession.new()
	var menu := ConfigMenu.new()
	menu.session = session
	root.add_child(menu)
	menu.reset()
	var expected: Array = []
	for line in FileAccess.get_file_as_string("res://../evidence/config/original/options.log").split("\n"):
		var fields := line.split("|")
		if fields.size() == 8 and fields[6] == "state": expected.append(fields[7])
	assert(expected.size() == 161)
	for tick in 161:
		var actual := "%d,%d,%d,%d,%d,%d,%s,%d,%d" % [menu.selected, menu.levels.difficulty, menu.levels.quality, menu.levels.time, menu.levels.health, session.ai_level, session.render_quality, session.maxtime, session.maxhp]
		assert(actual == expected[tick], "Config source difference at %d: %s != %s" % [tick, actual, expected[tick]])
		var group := tick / 40
		var phase := tick % 40
		if group < 4:
			menu.selected = [2, 3, 4, 5][group]
			menu.key_down({"right": (phase < 14 and phase % 2 == 0) or phase == 34,
				"left": (phase >= 16 and phase < 32 and phase % 2 == 0) or phase == 34})
		menu.tick()
	menu.free()
	print("CONFIG_REFERENCE_SMOKE_OK snapshots=161")
	quit()
