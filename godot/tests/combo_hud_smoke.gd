extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var hud := ComboHud.new()
	root.add_child(hud)
	hud.load_spec("res://generated/main/hit_receive.json")
	var left: TimelinePreview = hud._boards[1]["preview"]
	var right: TimelinePreview = hud._boards[2]["preview"]
	assert(left.position.is_equal_approx(Vector2(5, 37.4)))
	assert(right.position.is_equal_approx(Vector2(455, 37.4)))
	hud.play(1, 2)
	assert(left.current_source_frame() == 10)
	assert(not hud.showing(1))
	hud.tick()
	assert(hud.displayed_hits(1) == 2)
	assert(left._instance_local_frames["个"]["local_start"] == 3)
	assert(left.hidden_instance_names.has("百"))
	assert(left.hidden_instance_names.has("十"))
	hud.play(2, 123)
	hud.tick()
	assert(right._instance_local_frames["百"]["local_start"] == 2)
	assert(right._instance_local_frames["十"]["local_start"] == 3)
	assert(right._instance_local_frames["个"]["local_start"] == 4)
	assert(right.hidden_instance_names.is_empty())
	for i in 7:
		hud.tick()
	if "--capture" in OS.get_cmdline_user_args():
		await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/combo-hud.png")
	for i in 39:
		hud.tick()
	assert(not hud.showing(1) and not hud.showing(2))
	assert(left.current_source_frame() == 1)
	hud.free()
	print("COMBO_HUD_SMOKE_OK")
	quit()
