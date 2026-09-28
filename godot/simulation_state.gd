extends RefCounted

# Deliberately excludes Objects, Callables and RIDs: duplicate(true) cannot turn
# a live object graph into an owned snapshot. Owners must encode stable IDs.
const FORMAT := "bvn-simulation-state"
const VERSION := 1
const MAX_DEPTH := 64
const BINARY_GRAPH_BUILD := "battle-local-pba-dict-flat-v2"


static func validate_value(value: Variant, path: String = "$", depth: int = 0) -> String:
	if depth > MAX_DEPTH:
		return path + ": cyclic or excessively nested state"
	match typeof(value):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING:
			return ""
		TYPE_FLOAT:
			return "" if is_finite(value) else path + ": non-finite number"
		TYPE_ARRAY:
			for index in value.size():
				var problem := validate_value(value[index], "%s[%d]" % [path, index], depth + 1)
				if not problem.is_empty():
					return problem
		TYPE_DICTIONARY:
			# Local rollback checkpoints keep their complete Variant graph bytes. This
			# one envelope is the only place packed bytes are accepted as state.
			if _is_binary_graph_snapshot(value):
				return ""
			for key in value:
				if not key is String:
					return path + ": state keys must be strings"
				var problem := validate_value(value[key], path + "." + key, depth + 1)
				if not problem.is_empty():
					return problem
		_:
			return path + ": unsupported state type " + type_string(typeof(value))
	return ""


static func canonical(value: Variant) -> Variant:
	if value is Dictionary:
		var result := {}
		var keys: Array = value.keys()
		keys.sort()
		for key in keys:
			result[key] = canonical(value[key])
		return result
	if value is Array:
		var result := []
		for item in value:
			result.append(canonical(item))
		return result
	return value


static func pack_state(build: String, frame: int, owners: Dictionary) -> Dictionary:
	var problem := ""
	if build == BINARY_GRAPH_BUILD and owners.size() == 1 and owners.get("graph") is PackedByteArray:
		for key in owners:
			if not key is String:
				problem = "state keys must be strings"
				break
	else:
		problem = validate_value(owners)
	if not problem.is_empty() or build.is_empty() or frame < 0:
		return {"error": problem if not problem.is_empty() else "Invalid build/frame"}
	# Variant bytes preserve signed 64-bit RNG state and distinguish null/false.
	return {"format": FORMAT, "version": VERSION, "build": build, "frame": frame,
		"owners": canonical(owners)}


static func validate_snapshot(snapshot: Variant, build: String, owner_names: Array) -> String:
	var problem := validate_value(snapshot)
	if not problem.is_empty():
		return problem
	if not snapshot is Dictionary or snapshot.get("format") != FORMAT or not snapshot.get("version") is int or snapshot.get("version") != VERSION:
		return "Unsupported simulation state format/version"
	if snapshot.get("build") != build or not snapshot.get("frame") is int or snapshot.frame < 0:
		return "Incompatible build or frame"
	if not snapshot.get("owners") is Dictionary or snapshot.owners.size() != owner_names.size():
		return "Incomplete state owners"
	for owner in owner_names:
		if not snapshot.owners.has(owner):
			return "Missing state owner: " + str(owner)
	return ""


static func fingerprint(snapshot: Dictionary) -> String:
	if not validate_value(snapshot).is_empty():
		return ""
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(var_to_bytes(canonical(snapshot)))
	return context.finish().hex_encode()


static func _is_binary_graph_snapshot(value: Dictionary) -> bool:
	if value.size() != 5 or value.get("format") != FORMAT or not value.get("version") is int or value.get("version") != VERSION:
		return false
	if value.get("build") != BINARY_GRAPH_BUILD or not value.get("frame") is int or value.frame < 0:
		return false
	var owners: Variant = value.get("owners")
	return owners is Dictionary and owners.size() == 1 and owners.get("graph") is PackedByteArray


static func first_difference(left: Variant, right: Variant, path: String = "$") -> String:
	if typeof(left) != typeof(right):
		return path + ": type differs"
	if left is Dictionary:
		var keys: Array = left.keys()
		for key in right:
			if not left.has(key):
				keys.append(key)
		keys.sort()
		for key in keys:
			if not left.has(key) or not right.has(key):
				return path + "." + str(key) + ": missing key"
			var difference := first_difference(left[key], right[key], path + "." + str(key))
			if not difference.is_empty():
				return difference
	elif left is Array:
		if left.size() != right.size():
			return path + ": array size differs"
		for index in left.size():
			var difference := first_difference(left[index], right[index], "%s[%d]" % [path, index])
			if not difference.is_empty():
				return difference
	elif left != right:
		return path + ": value differs"
	return ""
