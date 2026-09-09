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
		# Explicit fixture schedule; this does not assert whole-game load order.
		fighter.ai_source_state.apply_load()
		fighter.ai_source_state.apply_frame(1)
		fighter.energy = 0
	cpu.position = Vector2(400, -25)
	player.position = Vector2(200, -25)
	cpu.set_facing(-1)
	cpu.ai_source_state.values.merge({"goran": 100, "attran": 400, "jumpran": 400, "bisharan": 400, "defran": 400}, true)
	var host := AiControllerHost.new()
	host.configure(cpu, "res://generated/fighters/yihu/ai_controller")
	host.scope_lookup = func(_key: String) -> Variant: return null
	var unexpected: Array = []
	host.effects = func(name: String) -> void: unexpected.append(name)
	host.body_calls = func(name: String, _args: Array) -> void: unexpected.append(name)
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/yihu/ai_controller/controller.json"))
	var path: String = metadata.hooks[0].path
	host.synchronize(0)
	host.dispatch([path], 0)
	assert(cpu.position.x == 400)
	host.dispatch([path], 1)
	assert(cpu.position.x == 394)
	assert(cpu.action == "走" and cpu.current_source_frame() == 10)
	# The walking target retains the source controller. Its next callback runs.
	cpu.run_frame_actions()
	host.dispatch([path], 2)
	assert(cpu.position.x == 388)
	assert(unexpected.is_empty())
	# Attack wins before the cached walk write when goto removes the controller.
	player.position.x = cpu.position.x - 30
	cpu.ai_source_state.values["attran"] = 0
	var before := cpu.position.x
	host.dispatch([path], 3)
	assert(cpu.action == "砍1" and cpu.current_source_frame() == 173)
	assert(cpu.position.x == before)
	host.dispatch([path], 4)
	assert(cpu.position.x == before)
	assert(unexpected.is_empty())
	# Wrapper moveX has no clamp; BODY clamps separately on its source callback.
	var wrapper_adapter := AiControllerHost.Adapter.new()
	wrapper_adapter.host_ref = weakref(host)
	cpu.position.x = 20
	cpu.facing = -1
	wrapper_adapter.move_axis("moveX", 6)
	assert(cpu.position.x == 14)
	# goto queues the target DoAction; stand's writes must not run in the caller.
	cpu.hited = 7
	cpu.beida = 7
	cpu.ai_source_state.values["hited"] = 7
	cpu.ai_source_state.values["beida"] = 7
	# AImain's authored placement survives the target jump at the same depth.
	cpu.set_instance_clip_frame("AImain", 2, false)
	host.goto_label("站立", false)
	assert(cpu.instance_clip_frame("AImain") == 2)
	assert(cpu.current_source_frame() == 1 and not cpu.timeline_playing)
	assert(cpu.hited == 7 and cpu.beida == 7)
	assert(cpu.ai_source_state.read_field("hited") == 7)
	cpu.run_frame_actions()
	assert(cpu.hited == 0 and cpu.beida == 0)
	assert(cpu.ai_source_state.read_field("hited") == 0)
	host.instances.clear()
	cpu.queue_free()
	player.queue_free()
	print("AI_HOST_SMOKE_OK")
	quit()
