class_name CommandCatalog
extends RefCounted

## Source-label move table compiled from doAllAction / timeline labels.
## IDs are the original frame labels (`砍1`, `万解`). New fighters only need
## their combat.json catalog; runtime does not hardcode per-character moves.

var _data: Dictionary = {}
var _entries_by_label: Dictionary = {}


func _init(combat: Dictionary = {}) -> void:
	load_combat(combat)


func load_combat(combat: Dictionary) -> void:
	_data = combat.get("command_catalog", {})
	_entries_by_label.clear()
	for entry: Dictionary in _data.get("entries", []):
		_entries_by_label[str(entry["label"])] = entry


func has_label(label: String) -> bool:
	return _entries_by_label.has(label)


func entry(label: String) -> Dictionary:
	return _entries_by_label.get(label, {})


func is_wired(label: String) -> bool:
	return str(entry(label).get("implementation", "")) == "wired"


func labels() -> PackedStringArray:
	var result := PackedStringArray()
	for label in _entries_by_label.keys():
		result.append(str(label))
	result.sort()
	return result


func gaps() -> Array:
	return _data.get("gaps", [])


func unimplemented_labels() -> PackedStringArray:
	var seen: Dictionary = {}
	for item: Dictionary in gaps():
		if str(item.get("kind", "")) != "command":
			continue
		var label := str(item.get("label", ""))
		if label != "":
			seen[label] = true
	var result := PackedStringArray(seen.keys())
	result.sort()
	return result


func match_context(
	context: String, input_state: Dictionary, energy: float, wired_only: bool = true
) -> Dictionary:
	var best: Dictionary = {}
	var best_priority := 1_000_000
	for entry: Dictionary in _data.get("entries", []):
		if wired_only and str(entry.get("implementation", "")) != "wired":
			continue
		if context not in entry.get("contexts", []):
			continue
		var slot := str(entry.get("slot", ""))
		if slot == "" or not _predicate_matches(slot, input_state, energy):
			continue
		var priority := 999
		var configured_priority: Variant = entry.get("dispatch_priority")
		if configured_priority != null:
			priority = configured_priority
		if priority < best_priority:
			best_priority = priority
			best = entry
	return best


func predicate_table(name: String) -> Dictionary:
	var predicates: Dictionary = _data.get("predicates", {})
	return predicates.get(name, {})


func _predicate_matches(name: String, input_state: Dictionary, energy: float) -> bool:
	var pred := predicate_table(name)
	if pred.is_empty():
		return false
	if energy < float(pred.get("energy_min", 0)):
		return false
	for button in pred.get("buttons_all", []):
		if not bool(input_state.get(str(button), false)):
			return false
	for button in pred.get("buttons_none", []):
		if bool(input_state.get(str(button), false)):
			return false
	return true
