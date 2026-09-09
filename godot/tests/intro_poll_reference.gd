extends SceneTree

class RecordingIntro extends BattleIntro:
	var called_steps: Array = []

	func _go_step(value: int) -> void:
		called_steps.append(value)
		super._go_step(value)


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1, "Pass the observed poll-inputs.json path")
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var fighters: Array[FighterRuntime] = []
	for name in ["minren", "yihu"]:
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/" + name
		root.add_child(fighter)
		fighters.append(fighter)
	var intro := RecordingIntro.new()
	root.add_child(intro)
	for case: Dictionary in fixture.cases:
		intro.begin(fighters, true, bool(case.loaded))
		intro.step = int(case.step)
		intro.called_steps.clear()
		# Unloaded source calls return before reading undefined fighter state.
		if case.loaded:
			for i in 2:
				assert(str(case.kcplayed[i]).is_valid_int())
				assert(str(case.frames[i]).is_valid_int())
				intro.states[i] = int(case.kcplayed[i])
				fighters[i].play_source_frame(int(case.frames[i]))
		var delivered := intro.deliver_recorded_poll(int(case.sequence), int(case.time_ms))
		assert(delivered)
		var expected: Array = case.called_steps.map(func(value): return int(value))
		assert(intro.called_steps == expected, "Original poll branch mismatch at %s" % case.sequence)
	intro.queue_free()
	for fighter in fighters:
		fighter.queue_free()
	await process_frame
	print("INTRO_POLL_REFERENCE_OK cases=", fixture.cases.size())
	quit()
