extends SceneTree

var observed: Array = []
var fighter: FighterRuntime


func _initialize() -> void:
	_run.call_deferred()


func _service(name: String, args: Array) -> Variant:
	assert(name == "frame_super" and args[0].op == "super_end" and args[0].kind == "cbsw")
	observed.append({"event": "super_end", "bs": int(fighter.ai_source_state.read_field("bs"))})
	return null


func _run() -> void:
	fighter = FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/byakuya"
	root.add_child(fighter)
	var driver := AiCpuDriver.new()
	driver.fighter = fighter
	driver.services = _service
	var fixtures: Array = JSON.parse_string(FileAccess.get_file_as_string(
		"res://../evidence/importer-loud-fail/r08/conditional-fixtures.json"))
	for fixture: Dictionary in fixtures:
		observed = []
		fighter.source_parent_values = fixture.parent_initial_values.duplicate(true)
		# A body field with the same spelling must not satisfy the parent test.
		fighter.ai_source_state.values["万解"] = true
		fighter.ai_source_state.values["bs"] = 91
		fighter.bs = 91
		driver._frame_service(fixture.calls[0])
		observed.append({"event": "false_result", "bs": int(fighter.ai_source_state.read_field("bs"))})
		driver._frame_service({"op": "parent_frame_field", "field_name": "万解", "value": true})
		driver._frame_service(fixture.calls[0])
		observed.append({"event": "true_result", "bs": int(fighter.ai_source_state.read_field("bs"))})
		assert(fighter.bs == 0)
		assert(observed.size() == fixture.expected.size())
		for index in observed.size():
			assert(observed[index].event == fixture.expected[index].event)
			assert(observed[index].bs == int(fixture.expected[index].bs))
		# Body state reset does not own the wrapper; this is not a full form switch.
		fighter.ai_source_state.configure(fighter.ai_source_state.spec)
		assert(fighter.read_parent_field("万解") == true)
	print("PARENT_FRAME_STATE_REFERENCE_OK 2/2 cases 6/6 observations")
	driver.free()
	fighter.queue_free()
	await process_frame
	quit()
