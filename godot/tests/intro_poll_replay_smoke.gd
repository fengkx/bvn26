extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var intro := BattleIntro.new()
	root.add_child(intro)
	intro.begin([], true, false)
	assert(intro.deliver_recorded_poll(1, 500))
	assert(intro.step == 0 and intro.clips.qjxg.current_source_frame() == 13)
	intro.fighters_loaded = true
	assert(intro.deliver_recorded_poll(2, 1036))
	assert(intro.step == 1)
	intro.begin([], true)
	# A replay must not invent interval callbacks while advancing visuals.
	for tick in 31:
		intro.tick(1.0 / 30)
	assert(intro.step == 0 and intro.poll_elapsed_ms == 0)
	assert(intro.deliver_recorded_poll(100, 500))
	assert(intro.step == 1 and intro.clips.qjxg.current_source_frame() == 20)
	intro.states = [1, 1]
	for tick in 16:
		intro.tick(1.0 / 30)
	assert(intro.last_poll_sequence == 100)
	assert(intro.deliver_recorded_poll(120, 1036))
	assert(intro.step == 1 and intro.last_poll_time_ms == 1036)
	assert(not intro.deliver_recorded_poll(119, 1037))
	assert(intro.poll_replay_error != "" and intro.last_poll_sequence == 120)
	intro.begin([], true)
	assert(intro.poll_replay_error == "" and intro.last_poll_sequence == -1)
	assert(intro.deliver_recorded_poll(1, 500))
	assert(not intro.deliver_recorded_poll(2, 499))
	intro.begin([], true)
	intro._go_step(4)
	assert(not intro.deliver_recorded_poll(1, 500))
	intro.cancel()
	assert(not intro.deliver_recorded_poll(2, 1000))
	intro.begin([])
	assert(not intro.deliver_recorded_poll(1, 500))
	intro.tick(0.5)
	assert(intro.step == 1)
	intro.queue_free()
	await process_frame
	print("INTRO_POLL_REPLAY_SMOKE_OK")
	quit()
