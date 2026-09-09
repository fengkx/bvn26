extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var player := FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/minren"
	var cpu := FighterRuntime.new()
	cpu.fighter_directory = "res://generated/fighters/yihu"
	cpu.player_slot = "p2"
	root.add_child(player)
	root.add_child(cpu)
	player.opponent = cpu
	cpu.opponent = player
	var driver := AiCpuDriver.new()
	root.add_child(driver)
	driver.configure(cpu, "res://generated/fighters/yihu/ai_controller", {}, -25, 1000,
		{"touchFloor": null}, func(name: String, _args: Array) -> Variant:
			assert(false, "Unexpected service: " + name)
			return null, true)
	var intro := BattleIntro.new()
	root.add_child(intro)
	for entry_frame in [6, 8]:
		intro.begin([player, cpu], true)
		intro.step = 2
		intro.states = [2, 0]
		driver.controller.goto_label("站立", true)
		driver.run_target_frames()
		for tick in entry_frame - 2:
			driver.advance_timeline()
			driver.run_target_frames()
		driver.advance_timeline()
		assert(cpu.current_source_frame() == entry_frame)
		# Deliver between timeline advance and queued DoAction execution.
		assert(intro.deliver_recorded_poll(100, 500))
		assert(intro.step == 3 and cpu.current_source_frame() == 822)
		driver.run_target_frames()
		if entry_frame == 8:
			# Retained frame 8 still executes goto stand after the external goto.
			assert(cpu.current_source_frame() == 1 and intro.states[1] == 0)
			assert(intro.deliver_recorded_poll(200, 1000))
			assert(intro.step == 3 and cpu.current_source_frame() == 822)
			driver.run_target_frames()
		else:
			assert(cpu.current_source_frame() == 822)
		driver.advance_timeline()
		intro.observe_fighter_frames()
		driver.run_target_frames()
		assert(cpu.current_source_frame() == 823 and intro.states[1] == 1)
	driver.stop()
	driver.queue_free()
	intro.queue_free()
	cpu.queue_free()
	player.queue_free()
	await process_frame
	print("INTRO_QUEUED_GOTO_SMOKE_OK")
	quit()
