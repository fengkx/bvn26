extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var cpu := FighterRuntime.new()
	cpu.fighter_directory = "res://generated/fighters/yihu"
	var player := FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/minren"
	root.add_child(cpu)
	root.add_child(player)
	await process_frame
	cpu.opponent = player
	player.opponent = cpu
	for fighter: FighterRuntime in [cpu, player]:
		fighter.ai_source_state.apply_load()
		fighter.ai_source_state.apply_frame(1)
	cpu.position = Vector2(400, -25)
	player.position = Vector2(200, -25)
	cpu.set_facing(-1)
	cpu.ai_source_state.values.merge({"goran": 100, "attran": 400, "jumpran": 400, "defran": 400, "bisharan": 400, "_lastX": 0}, true)
	var directory := "res://generated/fighters/yihu/ai_controller"
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("controller.json")))
	var path: String = metadata.hooks[0].path
	var driver := AiCpuDriver.new()
	root.add_child(driver)
	var services: Array = []
	var profile: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../spec/execution-profile.json"))
	driver.configure(cpu, directory, {}, -25, 1000, {"touchFloor": null},
		func(name: String, args: Array) -> Variant:
			services.append([name, args])
			return null,
		true)
	assert(cpu.source_body == driver.body)
	# Explicit fixture phases; whole-game callback ordering remains separate.
	driver.begin_display_tick(0)
	driver.run_controllers([path])
	assert(cpu.position.x == 400)
	for tick in [1, 2]:
		driver.prepare_display_tick(tick)
		driver.advance_timeline()
		driver.begin_display_tick(tick)
		driver.run_enter_frame(profile)
		# BODY stores the X produced by its child's movement in this same tick.
		assert(cpu.ai_source_state.read_field("_lastX") == cpu.position.x)
		driver.run_target_frames()
	assert(cpu.position.x == 388 and cpu.action == "走")
	await process_frame
	assert(is_instance_valid(cpu.ai_random_clock))
	assert(not cpu.ai_random_clock.is_queued_for_deletion())
	assert(services == [["receive", ["beida"]], ["receive", ["beida"]]])
	services.clear()
	# Route a compiled BODY callback through the driver, then its scheduled exit.
	cpu.energy = 200
	cpu.ai_source_state.values["goran"] = 0
	driver.body.doHurtSkill()
	assert(driver.timeouts.pending_count() == 1)
	assert(services == [["bsd", ["XG_bsq", false]]])
	assert(driver.timeouts.fire_recorded(1))
	assert(cpu.action == "招换" and services[2][0] == "addStgHit")
	var random := SourceRandom.new()
	random.use_live_random()
	driver.start_random(random, 5, true)
	assert(cpu.ai_random_clock.sample_count == 0)
	cpu.start_action("站立")
	await process_frame
	assert(cpu.ai_random_clock.fire_recorded(500))
	assert(cpu.ai_random_clock.sample_count == 1 and random.consumed.size() == 5)
	# Frame 725 has no goto/stop; without the guard callback it falls into
	# source frame 726 (防住), irrespective of the player guard-held flag.
	cpu.start_action("防御2")
	cpu.run_frame_actions()
	cpu.play_source_frame(725)
	cpu.timeline_playing = false
	driver.advance_timeline()
	assert(cpu.current_source_frame() == 725)
	cpu.timeline_playing = true
	driver.advance_timeline()
	assert(cpu.current_source_frame() == 726 and cpu.action == "防住")
	# The end of the 防住 label is not a stand-up command either. This skips
	# frame 735's explicit goto deliberately to test only sequential playback.
	cpu.play_source_frame(737)
	driver.advance_timeline()
	assert(cpu.current_source_frame() == 738 and cpu.action == "被打")
	# Source frame 738 explicitly plays; 744 stops; 748 writes then jumps
	# to stand and plays, whose frame-1 writes drain in the same target phase.
	cpu.timeline_playing = false
	driver.run_target_frames()
	assert(cpu.timeline_playing)
	cpu.play_source_frame(744)
	driver.run_target_frames()
	assert(not cpu.timeline_playing)
	driver.advance_timeline()
	assert(cpu.current_source_frame() == 744)
	cpu.play_source_frame(748)
	driver.run_target_frames()
	assert(cpu.current_source_frame() == 1 and cpu.action == "站立" and cpu.timeline_playing)
	assert(cpu.ai_source_state.read_field("hited") == 0)
	assert(cpu.ai_source_state.read_field("jumped") == 1)
	assert(cpu._ai_pending_frames.is_empty())
	driver.stop()
	assert(cpu.source_body == null)
	assert(cpu.ai_random_clock.registered_ms == -1)
	assert(driver.controller.fighter == null)
	driver.queue_free()
	cpu.queue_free()
	player.queue_free()
	print("AI_CPU_DRIVER_SMOKE_OK")
	quit()
