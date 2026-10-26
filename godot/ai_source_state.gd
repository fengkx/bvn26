class_name AiSourceState
extends RefCounted

var spec: Dictionary
var values: Dictionary = {}


func configure(model: Dictionary) -> void:
	spec = model
	values.clear()
	# An uninitialized `var sw;` does not overwrite sw when frame 1 repeats.
	# It only starts absent on a newly loaded fighter timeline.
	for key: String in spec["undefined_declarations"]:
		values[key] = null
	apply_frame(1)


func apply_frame(frame: int) -> void:
	_apply(spec["frame_writes"].get(str(frame), []))
	if spec.has("initialization_state"):
		var initial: Dictionary = spec["initialization_state"]
		if frame == int(initial["frame"]) and not values.get(initial["guard"]):
			_apply(initial["writes"])


func apply_write(event: Dictionary) -> void:
	_apply([event])


func apply_function(name: String) -> void:
	assert(spec["function_writes"].has(name), "Uncompiled state writer: " + name)
	_apply(spec["function_writes"][name])


func apply_load() -> void:
	# The schedule host decides when load runs relative to frame DoAction.
	_apply(spec["load_writes"])


func _apply(events: Array) -> void:
	for event: Dictionary in events:
		var operation := str(event.get("op", "write"))
		var field := str(event.get("field", ""))
		assert(not field.is_empty(), "Source-state event is missing its field")
		match operation:
			"write":
				assert(event.has("value") or event.has("read_field"), "Source-state write has no value")
				values[field] = values.get(event["read_field"]) if event.has("read_field") else event["value"]
			"increment":
				assert(values.has(field) and (values[field] == null or values[field] is int or values[field] is float),
					"Source-state increment requires a declared numeric/undefined field: " + field)
				assert(event.get("delta") is int or event.get("delta") is float,
					"Source-state increment has a non-numeric delta")
				# AVM1 ToNumber(undefined) is NaN; never coerce an absent
				# initial value to zero to make the arithmetic continue.
				values[field] = NAN if values[field] == null else values[field] + event["delta"]
			_:
				assert(false, "Unsupported source-state operation: " + operation)


func read_field(name: String) -> Variant:
	return values.get(name)
