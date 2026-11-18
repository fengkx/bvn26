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
	var queued_frames: Array[Callable] = []
	helper.source_child_frame_requested.connect(func(operation: Callable) -> void: queued_frames.append(operation))
	helper.bind_source_frames(registry, 0)
	helper.activate({"x": 280.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	# Settle activation before counting the two placement callbacks below.
	assert(queued_frames.size() == 1)
	queued_frames.pop_front().call()
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
	print("queued_nested_callbacks=", queued_frames.size())
	assert(queued_frames.size() == 2, "nested callbacks did not preserve FIFO requests")
	# A later goto in the same generation does not cancel the earlier target
	# script; it must still apply the captured frame's source writes.
	helper.play_source_frame(93)
	for operation: Callable in queued_frames:
		operation.call()
	assert(is_equal_approx(helper.position.x, defender.position.x), "queued target frame write was lost after a later goto")
	var stale_generation := helper._activation_generation
	var stale := helper._run_deferred_frame.bind(92, stale_generation)
	helper.deactivate()
	helper.activate({"x": 280.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	stale.call()
	assert(helper.current_source_frame() == 2, "deactivated generation retained a queued frame script")
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
	# A nested goto already queued in this generation must run before a later
	# root gotoAndStop(1); the root stop then invalidates that generation.
	queued_frames.clear()
	helper.activate({"x": 280.0, "y": -25.0, "facing": 1, "start_frame": 2}, owner)
	queued_frames.pop_front().call()
	var nested_generation := helper._activation_generation
	var nested_marker := {"ran": false}
	var nested_operation := func() -> void:
		nested_marker["ran"] = true
		helper._run_deferred_frame(92, nested_generation)
	# Capture the root-stop operation, then place an earlier nested operation
	# ahead of it to model the shared source sequence explicitly.
	helper._queue_root_stop()
	var root_stop_operation: Callable = queued_frames.pop_back()
	queued_frames.append(nested_operation)
	queued_frames.append(root_stop_operation)
	assert(queued_frames.size() == 2, "root stop did not enter the shared source FIFO")
	nested_operation.call()
	assert(nested_marker["ran"] and helper.attacking, "same-generation nested goto was discarded")
	root_stop_operation.call()
	assert(not helper.attacking and helper.current_source_frame() == 1, "root stop did not terminate after queued goto")
	helper.unbind_source_frames()
	assert(registry.size() == 0)
	print("YOU_HELPER_CALLBACK_ORDER_OK frame48_wait=1 frame92_dispatch=2")
	helper.queue_free()
	owner.queue_free()
	defender.queue_free()
	await process_frame
	quit()
