extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var owner := FighterRuntime.new()
	owner.fighter_directory = "res://generated/fighters/sasuke"
	var defender := FighterRuntime.new()
	defender.fighter_directory = "res://generated/fighters/yihu"
	var helper := HelperRuntime.new()
	helper.helper_directory = "res://generated/helpers/you"
	root.add_child(owner)
	root.add_child(defender)
	root.add_child(helper)
	await process_frame
	owner.opponent = defender
	defender.opponent = owner
	var registry := SourceCallbackRegistry.new()
	helper.bind_source_frames(registry, 0)
	helper.activate({"x": 280.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	helper.play_source_frame(48)
	# Keep two source-keyed callbacks on one placement to exercise full cleanup.
	var duplicate_contact: Dictionary = helper._combat.contact_gotos[0].duplicate()
	duplicate_contact["source_path"] = "synthetic/second-nested-callback.as"
	duplicate_contact["source_sha256"] = "synthetic-second-callback"
	helper._combat.contact_gotos.append(duplicate_contact)
	helper._sync_nested_callbacks()
	var contact: Dictionary = helper._combat.contact_gotos[0]
	assert(registry.size() == 3)
	# The placement tick must not run its enterFrame callback in the same dispatch.
	registry.dispatch(1)
	assert(helper.current_source_frame() == 48, "frame 48 callback fired during placement dispatch")
	# MOVE keeps the same child generation and callback registration alive.
	helper.play_source_frame(49)
	helper._sync_nested_callbacks()
	assert(registry.size() == 3, "MOVE replaced a retained child callback")
	# Move the defender into the retained source clip only after frame 48.
	var clip := helper._contact_clip_bounds(contact)
	var body := defender.instance_global_bounds("bdmn")
	defender.position += clip.get_center() - body.get_center()
	registry.dispatch(2)
	assert(helper.current_source_frame() == 92, "frame 48 callback did not fire on the retained next tick")
	helper.deactivate()
	assert(registry.size() == 1, "deactivate leaked nested callback")
	helper.unbind_source_frames()
	assert(registry.size() == 0)
	# A new match must restart the shared phase clock before the first placement.
	registry.dispatch(17)
	registry.clear()
	assert(registry.current_tick == 0)
	helper.bind_source_frames(registry, 0)
	helper.activate({"x": 280.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	helper.play_source_frame(48)
	helper._sync_nested_callbacks()
	registry.dispatch(1)
	assert(helper.current_source_frame() == 48, "new-match placement was delayed by stale registry tick")
	helper.unbind_source_frames()
	assert(registry.size() == 0)
	print("YOU_HELPER_CALLBACK_ORDER_OK frame48_wait=1 frame92_dispatch=2")
	helper.queue_free()
	owner.queue_free()
	defender.queue_free()
	await process_frame
	quit()
