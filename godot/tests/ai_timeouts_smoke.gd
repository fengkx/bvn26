extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var clock := AiSourceTimeouts.new()
	clock.recorded = true
	root.add_child(clock)
	var events: Array = []
	var nested: Array = []
	var first := clock.schedule(func() -> void:
		events.append("first")
		nested.append(clock.schedule(func() -> void: events.append("nested"), 600))
	, 800)
	var cancelled := clock.schedule(func() -> void: events.append("cancelled"), 600)
	assert(events.is_empty() and clock.pending_count() == 2)
	assert(clock.cancel(cancelled))
	assert(not clock.fire_recorded(cancelled))
	assert(clock.fire_recorded(first))
	assert(not clock.fire_recorded(first))
	assert(clock.pending_count() == 1 and events == ["first"])
	assert(clock.fire_recorded(nested[0]))
	assert(events == ["first", "nested"] and clock.pending_count() == 0)
	clock.recorded = false
	clock.schedule(func() -> void: events.append("live"), 20)
	paused = true
	Engine.time_scale = 0.01
	await create_timer(0.1, true, false, true).timeout
	Engine.time_scale = 1.0
	paused = false
	assert(events == ["first", "nested", "live"])
	clock.schedule(func() -> void: events.append("cleared"), 20)
	clock.clear()
	await create_timer(0.05).timeout
	assert(events.size() == 3 and clock.pending_count() == 0)
	clock.queue_free()
	print("AI_TIMEOUTS_SMOKE_OK")
	quit()
