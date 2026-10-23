extends SceneTree

# Isolated playhead comparison, matching build_numeric_goto_probe.py. Movement
# callbacks are paused; original Rukia frame calls remain enabled.
func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/rukia"
	root.add_child(fighter)
	var driver := AiCpuDriver.new()
	root.add_child(driver)
	driver.configure(fighter, "res://generated/fighters/rukia/player_controller", {}, -25, 1000,
		{"touchFloor": null}, func(_name: String, _args: Array) -> Variant: return null)
	fighter.ai_timeline_controlled = true
	fighter._ai_pending_frames.clear()
	fighter.ai_source_state.values["touch"] = false
	fighter.ai_source_state.values["speed"] = 0
	fighter.ai_source_state.values["khit"] = 73
	driver.controller.goto_frame(130, true)
	fighter.run_frame_actions()
	var rows: Array[int] = [fighter.current_source_frame()]
	for tick in range(1, 31):
		fighter.diagnostic_tick = tick
		fighter.advance_ai_timeline()
		fighter.run_frame_actions()
		rows.append(fighter.current_source_frame())
		assert(fighter.ai_source_state.values["khit"] == 73,
			"Numeric goto must not replay frame 128's khit write")
	var reference: Array = JSON.parse_string(FileAccess.get_file_as_string(
		"res://../evidence/importer-loud-fail/r06/numeric-native/frames.json"))
	assert(rows.size() == reference.size())
	for index in rows.size():
		assert(rows[index] == int(reference[index]), "Native numeric goto playhead mismatch: " + str(rows))
	# A stopped destination must remain stopped, including same-frame requests.
	driver.controller.goto_frame(130, false)
	fighter.run_frame_actions()
	fighter.advance_ai_timeline()
	assert(fighter.current_source_frame() == 130 and not fighter.timeline_playing)
	var args := OS.get_cmdline_user_args()
	if not args.is_empty():
		var file := FileAccess.open(args[0], FileAccess.WRITE)
		file.store_string(JSON.stringify({"frames": rows, "native_matches": rows.size()}, "  "))
	print("NUMERIC_GOTO_REFERENCE_OK 31/31")
	driver.stop()
	driver.queue_free()
	fighter.queue_free()
	await process_frame
	quit()
