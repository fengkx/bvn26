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
