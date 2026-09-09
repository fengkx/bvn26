extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	var reference: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	var players: Dictionary = {}
	for name: String in reference["players"]:
		var setup: Dictionary = reference["players"][name]
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/" + setup["fighter"]
		root.add_child(fighter)
		fighter.position = Vector2(setup["x"], setup["y"])
		fighter.set_facing(int(setup["facing"]))
		fighter.play_source_frame(int(setup["frame"]))
		players[name] = fighter
	var cpu: FighterRuntime = players["p2"]
	var result := {}
	for name: String in reference["sensors"]:
		var bounds := cpu.ai_senses.local_bounds(name)
		result[name] = {
			"bounds": [bounds.position.x, bounds.position.y, bounds.end.x, bounds.end.y]
				if bounds.has_area() else null,
			"hit": cpu.ai_senses.hit(name, players["p1"]),
		}
	var file := FileAccess.open(args[1], FileAccess.WRITE)
	file.store_string(JSON.stringify(result, "", false, true))
	file.close()
	print("AI_GEOMETRY_REFERENCE_OK")
	for fighter: FighterRuntime in players.values():
		fighter.queue_free()
	quit()
