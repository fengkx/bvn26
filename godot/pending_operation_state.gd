extends RefCounted

const Values := preload("res://simulation_state.gd")


static func save(queue: Array, identify: Callable) -> Dictionary:
	var entries := []
	var previous := -1
	for entry in queue:
		if not entry is Dictionary or not entry.get("order") is int or entry.order <= previous:
			return {"error": "Invalid pending operation order"}
		var operation: Variant = entry.get("operation")
		if not operation is Callable or not operation.is_valid() or operation.get_unbound_arguments_count() != 0:
			return {"error": "Invalid pending operation"}
		var target: Object = operation.get_object()
		var method: StringName = operation.get_method()
		# Lambdas cannot be reconstructed from their captured locals. All current
		# source child operations are named methods with value-only bound args.
		if target == null or not target.has_method(method):
			return {"error": "Pending operation is not a reconstructible named method"}
		var id: Variant = identify.call(target)
		if not id is String or id.is_empty():
			return {"error": "Unresolved pending operation target"}
		var arguments: Array = operation.get_bound_arguments()
		var problem := Values.validate_value(arguments)
		if not problem.is_empty():
			return {"error": problem}
		entries.append({"order": entry.order, "target": id, "method": str(method),
			"arguments": arguments.duplicate(true)})
		previous = entry.order
	return {"version": 1, "entries": entries}


static func prepare(snapshot: Variant, resolve: Callable) -> Dictionary:
	var problem := Values.validate_value(snapshot)
	if not problem.is_empty():
		return {"error": problem}
	if not snapshot is Dictionary or snapshot.get("version") != 1 or not snapshot.get("entries") is Array:
		return {"error": "Unsupported pending operation state"}
	var queue: Array[Dictionary] = []
	var previous := -1
	for entry in snapshot.entries:
		if not entry is Dictionary or not entry.get("order") is int or entry.order <= previous:
			return {"error": "Invalid pending operation order"}
		if not entry.get("target") is String or not entry.get("method") is String or not entry.get("arguments") is Array:
			return {"error": "Invalid pending operation descriptor"}
		var target: Variant = resolve.call(entry.target)
		if not target is Object or not is_instance_valid(target) or not target.has_method(entry.method):
			return {"error": "Unresolved pending operation method"}
		queue.append({"order": entry.order,
			"operation": Callable(target, entry.method).bindv(entry.arguments.duplicate(true))})
		previous = entry.order
	return {"queue": queue}
