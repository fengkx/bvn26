extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	scene._enter_current_fight(4)
	# main.swf 1738: p2@7 < p1@9 < p2fz@11 < p1fz@13.
	assert(scene.ichigo.z_index < scene.naruto.z_index)
	assert(scene.naruto.z_index < scene.ichigo_helper.z_index)
	assert(scene.ichigo_helper.z_index < scene.naruto_helper.z_index)
	assert(scene.naruto_energy.helper_id == scene.naruto_helper.helper_id)
	assert(scene.ichigo_energy.helper_id == scene.ichigo_helper.helper_id)
	assert(scene.naruto_energy._portrait_texture != null)
	assert(scene.ichigo_energy._portrait_texture != null)
	# Exercise the same helper frame and mirrored placement in both directions.
	for direction in [1, -1]:
		scene.naruto_helper.activate({"x": scene.naruto.position.x - 20 * direction, "y": scene.naruto.position.y, "facing": direction}, scene.naruto)
		scene.naruto_helper.play_source_frame(44)
		scene.naruto_helper.enter_frame()
		await process_frame
		await process_frame
		for actor in [scene.naruto, scene.ichigo, scene.naruto_helper]:
			for child in actor.get_children():
				if child is Sprite2D or child is Polygon2D:
					assert(child.z_index == 0, "Nested SWF depths must not escape their actor")
	# Leave a visible reference pose for optional rendered screenshot capture.
	scene.naruto_helper.activate({"x": scene.naruto.position.x - 20, "y": scene.naruto.position.y, "facing": 1}, scene.naruto)
	scene.naruto_helper.play_source_frame(44)
	scene.naruto_helper.enter_frame()
	scene.naruto_helper.play_source_frame(60)
	scene.naruto_energy.energy = 300
	scene.ichigo_energy.energy = 300
	await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/bvn-helper-presentation.png")
	print("HELPER_PRESENTATION_SMOKE_OK")
	scene.queue_free()
	await process_frame
	quit()
