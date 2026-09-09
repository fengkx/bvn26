extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var intro := BattleIntro.new()
	root.add_child(intro)
	assert(intro.hud_frame == 1 and not intro.hud_playing)
	intro.goto_hud("in")
	assert(intro.hud_frame == 2)
	for frame in [3, 4, 5]:
		intro.tick(1.0 / 30)
		assert(intro.hud_frame == frame)
	assert(not intro.hud_playing)
	intro.tick(1.0 / 30)
	assert(intro.hud_frame == 5)
	intro.goto_hud("out")
	assert(intro.hud_frame == 6)
	var ys := [-662, -942, -1222, -1502, -1782]
	for frame in range(6, 11):
		assert(intro.hud_frame == frame)
		assert(intro.spec.hud_frames[str(frame)].matrix.translateY == ys[frame - 6])
		intro.tick(1.0 / 30)
	# Frame 10 has no stop/goto script; natural wrap reaches frame 1 stop.
	assert(intro.hud_frame == 1 and not intro.hud_playing)
	intro.tick(1.0 / 30)
	assert(intro.hud_frame == 1)
	intro.queue_free()
	await process_frame
	print("HUD_TIMELINE_SMOKE_OK")
	quit()
