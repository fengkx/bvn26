extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/minren"
	root.add_child(fighter)
	var rows: Array = JSON.parse_string(FileAccess.get_file_as_string(
		"res://../evidence/combat/move-boundary-validation/coordinates/reference.json"))
	for row in rows:
		var values: Array = row.values
		if row.kind == "set":
			fighter.source_x = values[0]
			fighter.source_y = values[0]
			assert(fighter.source_x == values[1] and fighter.source_y == values[2])
		else:
			if values[1] == 0:
				fighter.source_x = 300 * values[0]
				fighter.source_y = -25
			fighter.source_x += 14.4 * values[0]
			fighter.source_y -= 19.2
			assert(fighter.source_x == values[2] and fighter.source_y == values[3])
	fighter.queue_free()
	await process_frame
	print("COORDINATE_REFERENCE_OK ", rows.size())
	quit()
