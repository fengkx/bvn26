extends SceneTree
const SHADER = preload("res://tests/packed_matrix_rows.gdshader")
func _initialize() -> void:
	_run.call_deferred()
func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 1)
	var directory := args[0]
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("fixture.json")))
	assert(fixture.production_admitted == false)
	for batch in fixture.batches:
		var size := Vector2i(256, int(batch.height))
		var source := Image.create_from_data(size.x, size.y, false, Image.FORMAT_RGBA8, FileAccess.get_file_as_bytes(directory.path_join(batch.name + ".rgba")))
		var words := Image.create_from_data(6, size.y, false, Image.FORMAT_RGBAF, FileAccess.get_file_as_bytes(directory.path_join(batch.name + ".words")))
		var viewport := SubViewport.new()
		viewport.size = size
		viewport.transparent_bg = true
		viewport.world_2d = World2D.new()
		viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(viewport)
		var sprite := Sprite2D.new()
		sprite.centered = false
		sprite.texture = ImageTexture.create_from_image(source)
		var material := ShaderMaterial.new()
		material.shader = SHADER
		material.set_shader_parameter("source_bytes", sprite.texture)
		material.set_shader_parameter("matrix_words", ImageTexture.create_from_image(words))
		sprite.material = material
		viewport.add_child(sprite)
		for tick in 3:
			await process_frame
			await RenderingServer.frame_post_draw
		assert(viewport.get_texture().get_image().save_png(directory.path_join(batch.name + ".png")) == OK)
		viewport.queue_free()
		await process_frame
	print("PACKED_MATRIX_ROWS_OK batches=", fixture.batches.size())
	quit()
