class_name SourceCallbackRegistry
extends RefCounted

var _next_id: int = 0
var _entries: Dictionary = {}


func register(target: Object, method: StringName, placed_tick: int) -> int:
	_next_id += 1
	_entries[_next_id] = {"target": weakref(target), "method": method, "placed_tick": placed_tick}
	return _next_id


func unregister(id: int) -> void:
	_entries.erase(id)


func dispatch(display_tick: int) -> void:
	# Registration order is global, including callbacks in different subtrees.
	# Retained clips keep their position; new instances join the next dispatch.
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


func clear() -> void:
	_entries.clear()


func size() -> int:
	return _entries.size()
