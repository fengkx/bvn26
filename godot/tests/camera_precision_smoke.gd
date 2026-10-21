extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var evidence: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var rows: Array = evidence.rows
	var world := GameWorld.new()
	var p1 := Node2D.new()
	var p2 := Node2D.new()
	world.game_x = float(rows[0].x)
	world.game_y = float(rows[0].y)
	world.game_scale = float(rows[0].scale_percent) / 100.0
	for index in range(1, rows.size()):
		var previous: Dictionary = rows[index - 1]
		var expected: Dictionary = rows[index]
		p1.position = Vector2(previous.p1[0], previous.p1[1])
		p2.position = Vector2(previous.p2[0], previous.p2[1])
		world.focus = previous.focus
		world.enter_frame(p1, p2)
		assert(world.game_x == float(expected.x), "camera X tick %d" % expected.tick)
		assert(world.game_y == float(expected.y), "camera Y tick %d" % expected.tick)
		assert(GameWorld.store_scale(world.game_scale) == float(expected.matrix_scale), "camera scale tick %d" % expected.tick)
		assert(absf(world.game_scale * 100.0 - float(expected.scale_percent)) < 0.00000001)
	assert(GameWorld.store_scale(1.000015) == 1.0)
	assert(GameWorld.store_scale(1.000016) == 1.0000152587890625)
	world._game_scale_percent = 100.008
	var projected: float = world.game_scale
	world.game_scale = projected
	assert(world._game_scale_percent == 100.008, "Restoring a derived scale must not round-trip the native percentage")
	world.free()
	p1.free()
	p2.free()
	print("CAMERA_NATIVE_TRAJECTORY_OK ", rows.size())
	quit()
