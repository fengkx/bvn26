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
	# Stand/air/dash use the first matching goto. Source:
	# DefineSprite_16 enterFrame → doAllAction(); that helper is placed on
	# 站立/走. The first _parent.gotoAndPlay that leaves those frames removes
	# the caller, so later magichit1/bisha cannot overwrite 招3/上必杀.
	# Guard keeps later-wins: onDefence first goto pins 防御2 (same clip).
	var last_wins := context == "guard"
	var best: Dictionary = {}
	var best_order := -1
	var found := false
	for entry: Dictionary in _data.get("entries", []):
		if wired_only and str(entry.get("implementation", "")) != "wired":
			continue
		if context not in entry.get("contexts", []):
			continue
		var slot := str(entry.get("slot", ""))
		if slot == "" or not _predicate_matches(slot, input_state, energy):
			continue
		var order := _dispatch_order_for(entry, context)
		if not found:
			found = true
			best_order = order
			best = entry
			continue
		if last_wins and order >= best_order:
			best_order = order
			best = entry
		elif not last_wins and order < best_order:
			best_order = order
			best = entry
	return best


func match_cancel(
	action: String, frame: int, input_state: Dictionary, energy: float
) -> Dictionary:
	# Later if(pred) goto in the same enterFrame clip wins.
	var best: Dictionary = {}
	var best_order := -1
	var found := false
	for window: Dictionary in _data.get("cancel_windows", []):
		if str(window.get("kind", "")) != "input":
			continue
		if str(window.get("implementation", "")) != "wired":
			continue
		if str(window.get("from", "")) != action:
			continue
		if frame < int(window.get("start_frame", 0)):
			continue
		if window.has("end_frame") and frame > int(window["end_frame"]):
			continue
		var pred := str(window.get("predicate", ""))
		if pred == "" or not _predicate_matches(pred, input_state, energy):
			continue
		var order := int(window.get("dispatch_order", 0))
		if not found or order >= best_order:
			found = true
			best_order = order
			best = window
	return best


func _dispatch_order_for(entry: Dictionary, context: String) -> int:
	var orders: Variant = entry.get("dispatch_orders")
	if typeof(orders) == TYPE_DICTIONARY and orders.has(context):
		return int(orders[context])
	var configured: Variant = entry.get("dispatch_order")
	if configured != null:
		return int(configured)
	var priority: Variant = entry.get("dispatch_priority")
	if priority != null:
		return int(priority)
	return -1


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
