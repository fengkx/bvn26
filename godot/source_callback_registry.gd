class_name SourceCallbackRegistry
extends RefCounted

var _next_id: int = 0
var _entries: Dictionary = {}
var current_tick: int = 0
var _dispatching: bool = false


func register(target: Object, method: StringName, placed_tick: int) -> int:
	_next_id += 1
	_entries[_next_id] = {"target": weakref(target), "method": method, "placed_tick": placed_tick}
	return _next_id


func unregister(id: int) -> void:
	_entries.erase(id)


func dispatch(display_tick: int) -> void:
	# Registration order is global, including callbacks in different subtrees.
	# Retained clips keep their position; new instances join the next dispatch.
	current_tick = display_tick
	_dispatching = true
	var pending := _entries.keys()
	pending.reverse()
	for id: int in pending:
		if not _entries.has(id):
			continue
		var entry: Dictionary = _entries[id]
		if int(entry["placed_tick"]) >= display_tick:
			continue
		var target: Object = entry["target"].get_ref()
		if target == null:
			_entries.erase(id)
			continue
		target.call(entry["method"])
	_dispatching = false


func registration_tick() -> int:
	# Placement happens before dispatch; enterFrame placement happens during
	# dispatch. Use the shared phase so both obey the next-dispatch rule.
	return current_tick if _dispatching else current_tick + 1


func clear() -> void:
	_entries.clear()
	current_tick = 0
	_dispatching = false


func size() -> int:
	return _entries.size()


func save_state(identify: Callable) -> Dictionary:
	if _dispatching:
		return {"error": "Cannot snapshot during callback dispatch"}
	var entries := []
	for id in _entries:
		var entry: Dictionary = _entries[id]
		var target: Object = entry.target.get_ref()
		if target == null:
			return {"error": "Unresolved callback target: %d" % id}
		var identity: Variant = identify.call(target)
		if not identity is String or identity.is_empty():
			return {"error": "Callback target has no stable identity: %d" % id}
		entries.append({"id": id, "target": identity, "method": str(entry.method),
			"placed_tick": entry.placed_tick})
	return {"version": 1, "next_id": _next_id, "current_tick": current_tick, "entries": entries}


func load_state(state: Variant, resolve: Callable) -> String:
	if _dispatching:
		return "Cannot restore during callback dispatch"
	if not state is Dictionary or state.get("version") != 1 or not state.get("entries") is Array:
		return "Unsupported callback registry state"
	for field in ["next_id", "current_tick"]:
		if not state.get(field) is int or state[field] < 0:
			return "Invalid registry field: " + field
	var restored := {}
	var previous := 0
	for entry in state.entries:
		if not entry is Dictionary or not entry.get("id") is int or not entry.get("placed_tick") is int:
			return "Invalid callback entry"
		if entry.id <= previous or entry.id > state.next_id or entry.placed_tick < 0:
			return "Invalid callback registration order"
		if not entry.get("target") is String or not entry.get("method") is String:
			return "Invalid callback reference"
		var target: Variant = resolve.call(entry.target)
		if not target is Object or not is_instance_valid(target) or not target.has_method(entry.method):
			return "Unresolved callback: " + entry.target + "." + entry.method
		restored[entry.id] = {"target": weakref(target), "method": StringName(entry.method),
			"placed_tick": entry.placed_tick}
		previous = entry.id
	# Resolve everything first. A bad reference must leave the live registry intact.
	_entries = restored
	_next_id = state.next_id
	current_tick = state.current_tick
	return ""
