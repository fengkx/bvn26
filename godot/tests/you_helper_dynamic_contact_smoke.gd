extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _new_actor(script: Script, directory: String) -> Node:
	var actor = script.new()
	actor.fighter_directory = directory
	return actor


func _run() -> void:
	var owner: FighterRuntime = _new_actor(FighterRuntime, "res://generated/fighters/kakashi")
	var defender: FighterRuntime = _new_actor(FighterRuntime, "res://generated/fighters/sasuke")
	var helper := HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/you"
	helper.fighter_directory = helper.helper_directory
	helper.autoplay = false
	root.add_child(owner)
	root.add_child(defender)
	root.add_child(helper)
	await process_frame
	owner.opponent = defender
	defender.opponent = owner
	defender.source_x = 480.0
	defender.source_y = 0.0
	defender.set_facing(-1)
	defender.start_action("站立")
	var registry := SourceCallbackRegistry.new()
	helper.bind_source_frames(registry, 0)
	helper.activate({"x": 280.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	var contact_frame := -1
	for display_tick in range(1, 70):
		helper.advance_timeline()
		registry.dispatch(display_tick)
		if helper.current_source_frame() == 92:
			contact_frame = helper._nested_dispatch_frame
			break
	assert(contact_frame == 50,
		"depth-3 MOVE at source frame 50 must extend atm1 to fixed target x=480; got %d" % contact_frame)
	print("YOU_HELPER_DYNAMIC_CONTACT_OK source_contact_frame=50 helper280 target480")

	helper.deactivate(false)
	defender.source_x = 300.0
	defender.source_y = 0.0
	defender.set_facing(1)
	defender.start_action("站立")
	helper.activate({"x": 500.0, "y": -25.0, "facing": -1, "start_frame": 2}, owner)
	contact_frame = -1
	for offset in range(1, 70):
		helper.advance_timeline()
		registry.dispatch(registry.current_tick + 1)
		if helper.current_source_frame() == 92:
			contact_frame = helper._nested_dispatch_frame
			break
	assert(contact_frame == 50,
		"mirrored depth-3 MOVE must extend atm1 to fixed target x=300; got %d" % contact_frame)
	print("YOU_HELPER_DYNAMIC_CONTACT_MIRROR_OK source_contact_frame=50 helper500 target300")
	helper.unbind_source_frames()
	helper.queue_free()
	owner.queue_free()
	defender.queue_free()
	await process_frame
	quit()
