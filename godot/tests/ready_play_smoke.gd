extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var intro := BattleIntro.new()
	root.add_child(intro)
	intro.begin([])
	var cleared: Array = []
	intro.interval_cleared.connect(func(name: String): cleared.append(name))
	intro._go_step(4)
	assert(intro.clips.ready.current_source_frame() == 1)
	assert(intro.playing.ready and not intro.hud_visible and cleared.is_empty())
	intro.tick(1.0 / 30)
	assert(intro.clips.ready.current_source_frame() == 2)
	assert(intro.hud_visible and intro.hud_frame == 2)
	assert(cleared == ["kcint", "nxtfht"])
	intro._goto("ready", 126, true)
	intro.tick(1.0 / 30, false, true)
	assert(intro.clips.ready.current_source_frame() == 127 and intro.active)
	intro.run_frame_actions()
	assert(not intro.active)
	intro.queue_free()
	await process_frame
	print("READY_PLAY_SMOKE_OK")
	quit()
