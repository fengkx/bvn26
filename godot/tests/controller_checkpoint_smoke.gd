extends SceneTree

const Checkpoint := preload("res://controller_checkpoint.gd")
const Operations := preload("res://pending_operation_state.gd")
const Values := preload("res://simulation_state.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/yihu"
	var opponent := FighterRuntime.new()
	opponent.fighter_directory = "res://generated/fighters/minren"
	root.add_child(fighter)
	root.add_child(opponent)
	await process_frame
	fighter.opponent = opponent
	opponent.opponent = fighter
	fighter.position = Vector2(300, 0)
	opponent.position = Vector2(900, 0)
	fighter.ai_source_state.apply_load()
	fighter.ai_source_state.values["_lastX"] = 300
	var queue: Array[Dictionary] = []
	fighter.source_child_frame_requested.connect(func(operation: Callable) -> void:
		queue.append({"order": queue.size() + 1, "operation": operation}))
	var registry := SourceCallbackRegistry.new()
	var driver := AiCpuDriver.new()
	root.add_child(driver)
	driver.configure(fighter, "res://generated/fighters/yihu/ai_controller", {}, 0, 1000,
		{"touchFloor": null}, func(_name: String, _args: Array) -> Variant: return null, true, registry)
	var host: AiControllerHost = driver.controller
	host.synchronize(0)
	for instance in host.instances._instances.values():
		if instance.controller is AiControllerHost.Receiver: continue
		instance.controller.touchFloor = true
		instance.controller.js = 7
		instance.controller.state = {"marker": [null, false]}
	# Generated locals include undefined and mutable dictionaries. Restoring must
	# not re-read bind_adapter's scope or omit inherited predicate state.
	var initial := Checkpoint.save(host)
	assert(not initial.has("error"), str(initial))
	var prepared := Checkpoint.prepare(host, initial)
	assert(not prepared.has("error"), str(prepared))
	var local_count := 0
	for entry in initial.entries:
		if entry.kind != "controller": continue
		local_count += 1
		var controller: RefCounted = prepared.targets[Checkpoint.identity(entry.path, entry.generation)]
		for field in entry.state:
			assert(controller.get(field) == entry.state[field])
	assert(local_count > 0, "Generated controller locals must actually be exercised")
	var malformed := initial.duplicate(true)
	for entry in malformed.entries:
		if entry.kind == "controller":
			entry.state.state = 7
			break
	assert(Checkpoint.prepare(host, malformed).has("error"))
	prepared.clear()
	assert(Checkpoint.save(host) == initial)
	driver.prepare_display_tick(1)
	fighter.start_action("招1")
	fighter.play_source_frame(327)
	fighter.run_frame_actions()
	driver.begin_display_tick(1)
	driver.run_controllers(host.paths_by_descending_depth())
	driver.begin_display_tick(2)
	driver.run_controllers(host.paths_by_descending_depth())
	assert(fighter.instance_local_offset("zh1atm") == Vector2(18, 0))
	opponent.position += fighter.instance_global_bounds("zh1atm").get_center() - opponent.instance_global_bounds("bdmn").get_center()
	driver.begin_display_tick(3)
	driver.run_controllers(host.paths_by_descending_depth())
	assert(fighter.instance_clip_frame("zh1atm") == 5 and queue.size() == 1)
	var snapshot := Checkpoint.save(host)
	assert(not snapshot.has("error"), str(snapshot))
	assert(Values.validate_value(snapshot).is_empty())
	var identify := func(target: Object) -> String:
		if target == driver: return "driver"
		for path in host.instances._instances:
			var entry: Dictionary = host.instances._instances[path]
			if target == entry.controller:
				return Checkpoint.identity(path, entry.generation)
		return ""
	var registry_state := registry.save_state(identify)
	assert(not registry_state.has("error"), str(registry_state))
	var queued_state := Operations.save(queue, identify)
	assert(not queued_state.has("error"), str(queued_state))
	queue.pop_front().operation.call()
	assert(fighter.source_projectile_target_bounds("abcd").has_area())
	# Destroy and replace the source instance before restoring it. Keep only a
	# WeakRef in the test so a stale saved Callable cannot mask missing rebuilds.
	var old_reference: WeakRef = fighter.source_projectiles["zh1atm"]
	fighter.start_action("站立")
	host.synchronize(4)
	fighter.start_action("招1")
	fighter.play_source_frame(327)
	host.synchronize(4)
	assert(old_reference.get_ref() == null)
	var queue_size := queue.size()
	var fresh_offset := fighter.instance_local_offset("zh1atm")
	prepared = Checkpoint.prepare(host, snapshot)
	assert(not prepared.has("error"), str(prepared))
	assert(queue.size() == queue_size and fighter.instance_local_offset("zh1atm") == fresh_offset)
	# A malformed state fails during preparation, before touching the live graph.
	var invalid := snapshot.duplicate(true)
	invalid.entries[0].generation = invalid.next_generation + 1
	var before := Checkpoint.save(host)
	assert(Checkpoint.prepare(host, invalid).has("error"))
	assert(Checkpoint.save(host) == before)
	var resolve := func(id: String) -> Object:
		return driver if id == "driver" else prepared.targets.get(id)
	var restored_queue := Operations.prepare(queued_state, resolve)
	assert(not restored_queue.has("error"), str(restored_queue))
	assert(registry.load_state(registry_state, resolve).is_empty())
	Checkpoint.commit(host, prepared)
	assert(Checkpoint.save(host) == snapshot)
	assert(registry.save_state(identify) == registry_state)
	assert(queue.size() == queue_size)
	# The fighter timeline is a separate owner; this fixture restores its two
	# exercised playhead fields explicitly, not as a claimed whole-battle save.
	fighter.set_instance_clip_frame("zh1atm", 5, true)
	fighter.set_instance_local_offset("zh1atm", Vector2(18, 0))
	assert(fighter.source_projectile_target_bounds("zh1atm").has_area())
	restored_queue.queue[0].operation.call()
	assert(not fighter.source_projectile_target_bounds("zh1atm").has_area())
	assert(fighter.source_projectile_target_bounds("abcd").has_area())
	var renamed := Checkpoint.save(host)
	prepared = Checkpoint.prepare(host, renamed)
	Checkpoint.commit(host, prepared)
	assert(Checkpoint.save(host) == renamed)
	# Descriptors reject missing targets and anonymous captured closures.
	invalid = queued_state.duplicate(true)
	invalid.entries[0].target = "missing"
	assert(Operations.prepare(invalid, resolve).has("error"))
	assert(Operations.save([{"order": 1, "operation": func() -> void: pass}], identify).has("error"))
	# A removed projectile can still be retained by a pending bound call. It
	# must be rebuilt with its OLD generation and remain inactive after restore.
	var retired: RefCounted = fighter.source_projectiles["zh1atm"].get_ref()
	var stale := [{"order": 99, "operation": retired.run_frame_script.bind(5)}]
	var stale_identity := func(target: Object) -> String:
		return Checkpoint.identity(target.source_path, target.generation)
	var stale_state := Operations.save(stale, stale_identity)
	fighter.start_action("站立")
	host.synchronize(5)
	fighter.start_action("招1")
	fighter.play_source_frame(327)
	host.synchronize(5)
	var with_retired := Checkpoint.save(host, [retired])
	assert(not with_retired.has("error") and with_retired.retired.size() == 1)
	prepared = Checkpoint.prepare(host, with_retired)
	assert(not prepared.has("error"), str(prepared))
	var stale_prepared := Operations.prepare(stale_state, func(key: String) -> Object: return prepared.targets.get(key))
	assert(not stale_prepared.has("error"))
	Checkpoint.commit(host, prepared)
	stale_prepared.queue[0].operation.call()
	assert(fighter.source_projectile_target_bounds("zh1atm").has_area())
	assert(not fighter.source_projectile_target_bounds("abcd").has_area())
	assert(Checkpoint.save(host, [stale_prepared.queue[0].operation.get_object()]) == with_retired)
	stale.clear()
	stale_prepared.clear()
	retired = null
	prepared.clear()
	restored_queue.clear()
	queue.clear()
	driver.stop()
	driver.queue_free()
	fighter.queue_free()
	opponent.queue_free()
	await process_frame
	print("CONTROLLER_CHECKPOINT_SMOKE_OK generated_locals=restored projectile=recreated pending_rename=rebound registry=restored")
	quit()
