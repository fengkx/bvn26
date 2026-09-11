extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var world: GameWorld = load("res://game_world.gd").new()
	root.add_child(world)
	var helper: HelperRuntime = load("res://helper_runtime.gd").new()
	helper.helper_directory = "res://generated/helpers/you"
	helper.fighter_directory = helper.helper_directory
	helper.autoplay = false
	root.add_child(helper)
	await process_frame
	var left := Node2D.new()
	var right := Node2D.new()
	root.add_child(left)
	root.add_child(right)

	# Source DefineSprite_1991 clamps every gamePlayer, including a parked fz,
	# after its frame-1 script parks the clip at (-200, -200).
	helper.position = Vector2(-200.0, -200.0)
	helper.attacking = false
	world.enter_frame(left, right, [helper])
	assert(is_equal_approx(helper.position.x, 20.0))
	assert(is_equal_approx(helper.position.y, -200.0))

	helper.position.x = -40.0
	helper.attacking = true
	world.enter_frame(left, right, [helper])
	assert(is_equal_approx(helper.position.x, 20.0))
	helper.position.x = 990.0
	world.enter_frame(left, right, [helper])
	assert(is_equal_approx(helper.position.x, 970.0))

	print("GAME_WORLD_HELPER_CLAMP_OK")
	helper.queue_free()
	world.queue_free()
	left.queue_free()
	right.queue_free()
	await process_frame
	quit()
