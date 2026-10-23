extends SceneTree


class Target extends RefCounted:
	var count := 0
	var clock: AiSourceTimeouts
	var own_id := 0
	var cancel_self := false

	func run() -> void:
		count += 1
		if cancel_self:
			clock.cancel(own_id)


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var clock := AiSourceTimeouts.new()
	clock.recorded = true
	root.add_child(clock)
	var target := Target.new()
	target.clock = clock
	var transient := Target.new()
	var transient_ref: WeakRef = weakref(transient)
	var once := clock.schedule(transient.run, 10)
	transient = null
	assert(transient_ref.get_ref() != null)
	assert(clock.fire_recorded(once))
	assert(transient_ref.get_ref() == null)
	var first := clock.schedule(target.run, 1000, true)
	var second := clock.schedule(target.run, 1000, true)
	assert(first != second and target.count == 0)
	assert(clock.fire_recorded(first) and clock.fire_recorded(first))
	assert(target.count == 2 and clock.pending_count() == 2)
	assert(clock.cancel(first) and clock.fire_recorded(second))
	assert(not clock.fire_recorded(first) and target.count == 3)
	var identify := func(_object: Object) -> String: return "captured_function"
	var resolve := func(_key: String) -> Object: return target
	var snapshot := clock.save_state(identify)
	assert(snapshot.version == 2 and snapshot.repeats[str(second)])
	clock.clear()
	assert(clock.load_state(snapshot, resolve).is_empty())
	assert(clock.fire_recorded(second) and clock.fire_recorded(second))
	assert(clock.save_state(identify) == snapshot)
	for broken in [null, {}, {str(second): 1}, {"unknown": true}]:
		var invalid := snapshot.duplicate(true)
		invalid.repeats = broken
		assert(not clock.load_state(invalid, resolve).is_empty())
		assert(clock.save_state(identify) == snapshot)
	var missing := snapshot.duplicate(true)
	missing.erase("repeats")
	assert(not clock.load_state(missing, resolve).is_empty())
	# Legacy snapshots contain one-shot timeouts only.
	missing.version = 1
	assert(clock.load_state(missing, resolve).is_empty())
	assert(clock.fire_recorded(second) and not clock.fire_recorded(second))
	var self_cancel := clock.schedule(target.run, 1000, true)
	target.own_id = self_cancel
	target.cancel_self = true
	assert(clock.fire_recorded(self_cancel))
	assert(not clock.fire_recorded(self_cancel))
	target.cancel_self = false
	var cancel_on_signal := clock.schedule(target.run, 1000, true)
	clock.fired.connect(func(id: int) -> void:
		if id == cancel_on_signal: clock.cancel(id)
	)
	var before := target.count
	assert(not clock.fire_recorded(cancel_on_signal) and target.count == before)
	clock.recorded = false
	var live := clock.schedule(target.run, 10, true)
	paused = true
	Engine.time_scale = 0.01
	# Wait for deliveries rather than assuming the host renders multiple frames
	# in a fixed wall-clock window while the roster suite is running.
	for attempt in 120:
		await create_timer(0.02, true, false, true).timeout
		if target.count >= before + 2:
			break
	Engine.time_scale = 1.0
	paused = false
	assert(target.count >= before + 2)
	clock.cancel(live)
	before = target.count
	await create_timer(0.04).timeout
	assert(target.count == before and clock.pending_count() == 0)
	clock.free()
	print("REPEATING_TIMEOUTS_SMOKE_OK independent_ids retained cancel reentrant rollback live")
	quit()
