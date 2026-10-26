class_name SourceRootIntervals
extends AiSourceTimeouts

# Source handle fields belong to _root, not to the body that registered them.
# Assigning a field never cancels its former ID; only clearInterval does that.
var handles: Dictionary = {}


func assign_interval(slot: String, callback: Callable, delay_ms: int) -> int:
	assert(slot in ["feiint", "feiint2", "airanset"], "Uncompiled root interval field: " + slot)
	var id := schedule(callback, delay_ms, true)
	handles[slot] = id
	return id


func clear_interval(slot: String) -> bool:
	assert(slot in ["feiint", "feiint2", "airanset"], "Uncompiled root interval field: " + slot)
	# clearInterval(undefined), like an already cancelled numeric ID, is a no-op.
	# Cancellation does not write undefined back into the source handle field.
	return cancel(int(handles[slot])) if handles.has(slot) else false


func save_state(identify: Callable) -> Dictionary:
	var snapshot := super.save_state(identify)
	if not snapshot.has("error"):
		snapshot["root_handles"] = handles.duplicate()
	return snapshot


func load_state(snapshot: Variant, resolve: Callable) -> String:
	if not snapshot is Dictionary or not snapshot.get("root_handles") is Dictionary:
		return "Missing root interval handles"
	for slot in snapshot.root_handles:
		var id: Variant = snapshot.root_handles[slot]
		if slot not in ["feiint", "feiint2", "airanset"] or not id is int or id <= 0 or not snapshot.get("next_id") is int or id > snapshot.next_id:
			return "Invalid root interval handle"
	var error := super.load_state(snapshot, resolve)
	if error.is_empty():
		handles = snapshot.root_handles.duplicate()
	return error
