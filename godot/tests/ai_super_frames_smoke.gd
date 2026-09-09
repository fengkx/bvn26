extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var cpu := FighterRuntime.new()
	cpu.fighter_directory = "res://generated/fighters/yihu"
	cpu.player_slot = "p2"
	var player := FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/minren"
	root.add_child(cpu)
	root.add_child(player)
	await process_frame
	cpu.opponent = player
	player.opponent = cpu
	var services := AiCombatServices.new()
	services.fighter = cpu
	services.super_runtime = SuperRuntime.new()
	var presentation := SuperPresentation.new()
	presentation.load_spec("res://generated/main/hit_receive.json")
	services.super_runtime.presentation = presentation
	var requests: Array = []
	services.super_runtime.xg_requested.connect(func(clip: String, _pos: Vector2, _facing: int) -> void:
		requests.append([clip, presentation.face_label]))
	var driver := AiCpuDriver.new()
	root.add_child(driver)
	driver.configure(cpu, "res://generated/fighters/yihu/ai_controller", {}, 0, 1000,
		{"touchFloor": null}, services.invoke, true)
	for fixture in [["必杀", 450, 463, "XG_bs", "一户1"],
			["上必杀", 530, 542, "XG_bs", "一户1"],
			["超必杀", 585, 601, "XG_cbs", "一户2"]]:
		requests.clear()
		driver.controller.goto_label(fixture[0], true)
		driver.run_target_frames()
		cpu.play_source_frame(fixture[1])
		assert(not cpu.root_zhanting)
		driver.run_target_frames()
		assert(cpu.root_zhanting and player.root_zhanting and not player.timeline_playing)
		assert(requests == [[fixture[3], ""]])
		assert(presentation.face_label == fixture[4] and presentation.active_slot == "face_p2")
		assert(services.super_runtime.last_focus == ("p2" if fixture[0] == "超必杀" else "all"))
		driver.run_target_frames()
		assert(requests.size() == 1)
		cpu.play_source_frame(fixture[2])
		driver.run_target_frames()
		assert(not cpu.root_zhanting and not player.root_zhanting and player.timeline_playing)
		assert(presentation.face_label == "" and services.super_runtime.last_focus == "all")
	# Naruto frame 530 calls bsw before its literal bs=0 assignment.
	player.run_frame_actions()
	player.ai_timeline_controlled = true
	player.bs = 7
	player.ai_source_state.values["bs"] = 7
	var observed: Array = []
	player.ai_frame_service_requested.connect(func(event: Dictionary) -> void:
		observed.append([event["kind"], player.bs]))
	player.play_source_frame(530)
	player._apply_ai_source_frame()
	assert(observed == [["bsw", 7]])
	assert(player.bs == 0 and player.ai_source_state.read_field("bs") == 0)
	driver.stop()
	services.clear()
	driver.queue_free()
	cpu.queue_free()
	player.queue_free()
	await process_frame
	print("AI_SUPER_FRAMES_SMOKE_OK")
	quit()
