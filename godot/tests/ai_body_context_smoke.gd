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
		var state := AiSourceState.new()
		state.configure(fighter.ai_source_state.spec)
		assert(state.read_field("_lastX") == 0 and state.read_field("inited") == true)
		state.values["_lastX"] = 123
		state.apply_frame(1)
		assert(state.read_field("_lastX") == 123)
		state.configure(fighter.ai_source_state.spec)
		assert(state.read_field("_lastX") == 0)
	cpu.position = Vector2(100, -25)
	player.position = Vector2(700, -25)
	cpu.set_facing(-1)
	assert(cpu.ai_source_state.read_field("_lastX") == 0)
	assert(cpu.ai_source_state.read_field("inited") == true)
	cpu.ai_source_state.values["goran"] = 400
	var directory := "res://generated/fighters/yihu/ai_controller"
	var host := AiControllerHost.new()
	host.configure(cpu, directory)
	host.scope_lookup = func(_key: String) -> Variant: return null
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("body.json")))
	var context := AiBodyContext.new(cpu)
	context.configure(host, metadata, {8: Rect2(300, -50, 100, 0)})
	context.map_size_x = 1000
	context.floor_y = -25
	var calls: Array = []
	context.external_call = func(name: String, args: Array) -> Variant:
		calls.append([name, args])
		return null
	var body = load(directory.path_join("body.gd")).new({})
	body.adapter = context
	cpu.energy = 350
	body.on_enterframe()
	assert(cpu.energy == 300)
	assert(cpu.ai_source_state.read_field("touchFloor") == true)
	assert(cpu.ai_source_state.read_field("_lastX") == 100)
	# Re-entering frame 1 must not repeat the guarded first-load assignment.
	cpu.ai_source_state.apply_frame(1)
	assert(cpu.ai_source_state.read_field("_lastX") == 100)
	cpu.position = Vector2(350, -55)
	assert(body.isHitBan() == -50)
	assert(cpu.ai_source_state.read_field("i") == 8)
	body.on_enterframe()
	assert(cpu.position.y == -50)
	assert(cpu.ai_source_state.read_field("touch") == true)
	assert(cpu.ai_source_state.read_field("touchFloor") == false)
	cpu.ai_source_state.values["htx"] = 5
	body.fangyux()
	assert(cpu.position.x == 355)
	cpu.root_zhanting = true
	body.fangyux()
	assert(cpu.position.x == 355)
	# BODY clamp precedes the root-pause return.
	cpu.position.x = 1001
	cpu.energy = -1
	body.on_enterframe()
	assert(cpu.position.x == 970 and cpu.energy == 0)
	cpu.root_zhanting = false
	cpu.energy = 200
	cpu.ai_source_state.values["goran"] = 0
	body.doHurtSkill()
	assert(cpu.energy == 100)
	assert(calls == [["bsd", ["XG_bsq", false]], ["setTimeout", ["doHurtSkill_timeout_1", 600]]])
	assert(cpu.ai_source_state.read_field("hurtSkling") == true)
	body.doHurtSkill_timeout_1()
	assert(cpu.action == "招换")
	assert(calls[2] == ["bsw", [false]])
	assert(calls[3] == ["addStgHit", ["XG_baoqi", {"pw": 80, "zl": 5, "yup": 0, "hitx": 15, "hdtime": 0, "htype": "击飞"}]])
	var clock := AiSourceTimeouts.new()
	clock.recorded = true
	root.add_child(clock)
	context.timeout_scheduler = clock
	context.body_target = weakref(body)
	var registrations: Array = []
	clock.registered.connect(func(id: int, delay: int) -> void: registrations.append([id, delay]))
	calls.clear()
	cpu.ai_source_state.apply_frame(1)
	cpu.energy = 200
	body.doHurtSkill()
	assert(clock.pending_count() == 1 and registrations[0][1] == 600)
	assert(calls == [["bsd", ["XG_bsq", false]]])
	assert(clock.fire_recorded(registrations[0][0]))
	assert(clock.pending_count() == 0 and calls.size() == 3)
	assert(calls[1] == ["bsw", [false]] and calls[2][0] == "addStgHit")
	clock.queue_free()
	host.instances.clear()
	cpu.queue_free()
	player.queue_free()
	print("AI_BODY_CONTEXT_SMOKE_OK")
	quit()
