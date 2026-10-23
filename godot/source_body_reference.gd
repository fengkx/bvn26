class_name SourceBodyReference
extends RefCounted

var paths: Dictionary
var path: String


class CapturedFunction extends RefCounted:
	var receiver: RefCounted
	var method: StringName
	func invoke(arguments: Array = []) -> Variant:
		return receiver.callv(method, arguments)


func _init(root_paths: Dictionary = {}, source_path: String = "") -> void:
	paths = root_paths
	path = source_path


func resolve() -> FighterRuntime:
	var binding: WeakRef = paths.get(path)
	if binding == null:
		return null
	var wrapper: FighterRuntime = binding.get_ref()
	return wrapper if wrapper != null and wrapper.source_body_available else null


func same_path(other: SourceBodyReference) -> bool:
	# Flash references identify the source path, not a Godot body's node/object.
	return is_same(paths, other.paths) and path == other.path


func read_field(field: String) -> Variant:
	var wrapper := resolve()
	if wrapper == null:
		return null
	match field:
		"hp": return wrapper.health if wrapper.source_health_defined else null
		"ql": return wrapper.energy
		"_currentframe": return wrapper.current_source_frame()
	return wrapper.ai_source_state.read_field(field)


func write_field(field: String, value: Variant) -> void:
	var wrapper := resolve()
	assert(wrapper != null, "Write through an unresolved BODY path: " + path)
	match field:
		"hp":
			wrapper.health = float(value)
			wrapper.source_health_defined = true
		"ql": wrapper.energy = float(value)
		_: wrapper.ai_source_state.values[field] = value


func has_function(method: StringName) -> bool:
	var wrapper := resolve()
	return wrapper != null and wrapper.source_body != null and wrapper.source_body.has_method(method)


func capture_function(method: StringName) -> CapturedFunction:
	var wrapper := resolve()
	assert(wrapper != null and wrapper.source_body != null and wrapper.source_body.has_method(method), "Uncompiled live BODY function: " + str(method))
	var captured := CapturedFunction.new()
	captured.receiver = wrapper.source_body
	captured.method = method
	return captured


func call_current(method: StringName, arguments: Array) -> Variant:
	return capture_function(method).invoke(arguments)
