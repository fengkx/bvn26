class_name SourceFormContext
extends RefCounted

var fighter: FighterRuntime
var root_intervals: SourceRootIntervals
var root_values: Dictionary
var transfer: Dictionary = {}
var wrapper_name: String
var dispatch: Callable
var body_reference: SourceBodyReference


func _init(owner_fighter: FighterRuntime = null, intervals: SourceRootIntervals = null,
		shared_root_values: Dictionary = {}, source_name: String = "", effects: Callable = Callable()) -> void:
	if owner_fighter == null:
		# Rollback allocates the object graph before reconnecting its fields.
		assert(intervals == null and shared_root_values.is_empty() and source_name.is_empty() and not effects.is_valid())
		return
	assert(intervals != null and effects.is_valid())
	assert(source_name in ["p1", "p2"])
	fighter = owner_fighter
	root_intervals = intervals
	root_values = shared_root_values
	wrapper_name = source_name
	dispatch = effects
	if not root_values.has("body_paths"):
		root_values["body_paths"] = {}
	var path := "/game/" + source_name + "/mc"
	root_values.body_paths[path] = weakref(fighter)
	body_reference = SourceBodyReference.new(root_values.body_paths, path)


func read_field(key: String) -> Variant:
	match key:
		"transformed": return fighter.read_parent_field("万解")
		"transfer_hp": return transfer.get("hp")
		"transfer_ql": return transfer.get("ql")
		"wrapper_name": return wrapper_name
	assert(root_values.has(key), "Uncompiled form root field: " + key)
	return root_values[key]


func write_field(key: String, value: Variant) -> void:
	match key:
		"transformed": fighter.write_parent_field("万解", value)
		"transfer_hp": transfer["hp"] = value
		"transfer_ql": transfer["ql"] = value
		"trace": dispatch.call("trace", [value])
		"root_y":
			assert(root_values.has(key), "Uncompiled root coordinate")
			root_values[key] = value
			dispatch.call("root_y", [value])
		_:
			if key.begins_with("body_key:") or key.begins_with("body_field:"):
				fighter.ai_source_state.values[key.get_slice(":", 1)] = value
			else:
				assert(false, "Uncompiled form write: " + key)


func effect(operation: String) -> void:
	assert(operation in ["_parent.updateGJL()",
		"_root.game[\"p\" + pn].updateGJL()", "AImain.gotoAndStop(1)",
		"AImain.gotoAndStop(2)", "AImain.unloadMovie()"], "Uncompiled form effect: " + operation)
	# The owner must implement these against the loaded profile. This context
	# never treats a missing parent/controller consumer as a successful no-op.
	dispatch.call(operation, [])


func next_frame() -> bool:
	# Return false when nextFrame removes the executing body. Flash retires
	# its continuation immediately; wankai's following root_y write then never
	# runs. A no-op at the parent's last frame need not destroy that receiver.
	var retained: Variant = dispatch.call("_parent.nextFrame()", [])
	assert(retained is bool, "Parent replacement must report old receiver liveness")
	return retained
