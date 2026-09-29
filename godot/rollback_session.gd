extends RefCounted

# Input prediction and bounded correction, independent of the transport. The
# adapter owns complete checkpoints, timer delivery and presentation deduplication.
const State := preload("res://simulation_state.gd")
const BUTTONS := preload("res://keyboard_input_source.gd").BUTTONS

var error := ""
var frontier := 0
var confirmed := 0
var rollback_count := 0
var replayed_frames := 0
var epoch := ""
var profile := {
	"advance_count": 0, "advance_us": 0,
	"save_count": 0, "save_us": 0,
	"validate_count": 0, "validate_us": 0,
	"copy_count": 0, "copy_us": 0,
	"load_count": 0, "load_us": 0,
	"replay_advance_count": 0, "replay_advance_us": 0,
	"replay_save_count": 0,
	"saves_skipped_count": 0,
}
var _adapter: RefCounted
var _window := 0
var _capacity := 0
var _delay := 0
var _actual := {"p1": {}, "p2": {}}
var _used := {}
var _states := {}
var _anchors := {"p1": {}, "p2": {}}
var _build := ""
var _owners: Array = []
var _replaying := false


func configure(adapter: RefCounted, match_epoch: String, window: int, capacity: int, input_delay: int = 0) -> String:
	if _adapter != null:
		return "Session already configured"
	if match_epoch.is_empty() or window < 0 or input_delay < 0 or capacity < window + input_delay + 2:
		return "Invalid rollback history limits"
	for method in ["save_state", "validate_state", "load_state", "advance"]:
		if not adapter.has_method(method):
			return "Missing adapter method: " + method
	var snapshot: Dictionary = _profiled_save_state(adapter)
	if not _profiled_validate_value(snapshot).is_empty() or not snapshot.get("owners") is Dictionary:
		return "Adapter did not return owned value state"
	_build = snapshot.get("build", "")
	_owners = snapshot.owners.keys()
	var problem := _profiled_validate_snapshot(snapshot, _build, _owners)
	if not problem.is_empty() or snapshot.get("frame") != 0:
		return "Invalid initial snapshot: " + problem
	problem = _profiled_adapter_validate(adapter, snapshot)
	if not problem.is_empty():
		return problem
	_adapter = adapter
	epoch = match_epoch
	_window = window
	_capacity = capacity
	_delay = input_delay
	for frame in range(1, _delay + 1):
		for slot in ["p1", "p2"]:
			_actual[slot][frame] = _neutral()
	confirmed = _delay
	_states[0] = _profiled_copy_dictionary(snapshot, true)
	return ""


func receive(match_epoch: String, slot: String, frame: int, held: Dictionary) -> String:
	if not error.is_empty():
		return error
	if _adapter == null or match_epoch != epoch or slot not in ["p1", "p2"]:
		return "Wrong session or player slot"
	if not can_receive_frame(frame):
		return "Input outside retained/receive range"
	var problem := validate_input(held)
	if not problem.is_empty():
		return problem
	if _actual[slot].has(frame):
		return "" if _actual[slot][frame] == held else "Conflicting immutable input"
	_actual[slot][frame] = _profiled_copy_dictionary(held, true)
	if frame <= frontier and _used[frame][slot] != held:
		problem = _correct(frame)
		if not problem.is_empty():
			error = problem
			return error
	while _actual.p1.has(confirmed + 1) and _actual.p2.has(confirmed + 1):
		confirmed += 1
	_prune()
	return ""


func step() -> String:
	if not error.is_empty():
		return error
	if _adapter == null:
		return "Session not configured"
	if frontier + 1 > confirmed + _window:
		return "waiting_for_input"
	var problem := _advance_one()
	if not problem.is_empty() and problem not in ["waiting_for_confirmation", "match_finished"]:
		error = problem
	_prune()
	return problem


func state_at(frame: int) -> Dictionary:
	return _profiled_copy_dictionary(_states.get(frame, {}), true)


func oldest_frame() -> int:
	return int(_states.keys().min()) if not _states.is_empty() else 0


func can_receive_frame(frame: int) -> bool:
	return frame >= oldest_frame() + 1 and frame <= frontier + _capacity


func retained_bytes() -> int:
	return var_to_bytes([_states, _actual, _used, _anchors]).size()


func profile_counters() -> Dictionary:
	var counters: Dictionary = profile.duplicate(true)
	var adapter_counters := _adapter_profile_counters()
	for key in ["rebuild_count", "rebuild_us"]:
		var value: Variant = adapter_counters.get(key, 0)
		counters[key] = int(value) if value is int or value is float else 0
	return counters


static func validate_input(held: Dictionary) -> String:
	if held.size() != BUTTONS.size():
		return "Incomplete logical buttons"
	for button in BUTTONS:
		if not held.get(button) is bool:
			return "Invalid logical button: " + button
	return ""


func _input_for(slot: String, frame: int) -> Dictionary:
	if _actual[slot].has(frame):
		return _profiled_copy_dictionary(_actual[slot][frame], false)
	if _used.has(frame - 1):
		return _profiled_copy_dictionary(_used[frame - 1][slot], false)
	if not _anchors[slot].is_empty():
		return _profiled_copy_dictionary(_anchors[slot], false)
	return _neutral()


func _advance_one() -> String:
	var frame := frontier + 1
	var players := {"p1": _input_for("p1", frame), "p2": _input_for("p2", frame)}
	var adapter_players := _profiled_copy_dictionary(players, true)
	var advance_started_usec := Time.get_ticks_usec()
	var problem: String = _adapter.advance(frame, adapter_players)
	_record_profile_duration("replay_advance" if _replaying else "advance", advance_started_usec)
	if not problem.is_empty():
		return problem
	var snapshot: Dictionary = _profiled_save_state(_adapter)
	problem = _profiled_validate_snapshot(snapshot, _build, _owners)
	if not problem.is_empty() or snapshot.frame != frame:
		return "Adapter produced invalid snapshot at %d: %s" % [frame, problem]
	problem = _profiled_adapter_validate(_adapter, snapshot)
	if not problem.is_empty():
		return problem
	_used[frame] = players
	_states[frame] = _profiled_copy_dictionary(snapshot, true)
	frontier = frame
	return ""


func _correct(frame: int) -> String:
	if not _states.has(frame - 1):
		return "Missing pre-correction snapshot"
	var has_begin_hook := _adapter.has_method("begin_replay")
	var has_end_hook := _adapter.has_method("end_replay")
	if has_begin_hook != has_end_hook:
		return "Adapter replay hooks must be paired"
	_replaying = true
	if has_begin_hook:
		_adapter.call("begin_replay")
	var problem := _correct_replay(frame)
	if has_end_hook:
		_adapter.call("end_replay")
	_replaying = false
	return problem


func _correct_replay(frame: int) -> String:
	var snapshot: Dictionary = _profiled_copy_dictionary(_states[frame - 1], true)
	var problem: String = _profiled_adapter_validate(_adapter, snapshot)
	if not problem.is_empty(): return problem
	problem = _profiled_load_state(snapshot)
	if not problem.is_empty(): return problem
	var target := frontier
	frontier = frame - 1
	rollback_count += 1
	while frontier < target:
		problem = _advance_one()
		if problem in ["waiting_for_confirmation", "match_finished"]:
			for future in _states.keys():
				if future > frontier: _states.erase(future)
			for future in _used.keys():
				if future > frontier: _used.erase(future)
			return ""
		if not problem.is_empty():
			return problem
		replayed_frames += 1
	return ""


func _profiled_save_state(adapter: RefCounted) -> Dictionary:
	var started_usec := Time.get_ticks_usec()
	var snapshot: Dictionary = adapter.save_state()
	_record_profile_duration("save", started_usec)
	if _replaying:
		profile.replay_save_count += 1
	return snapshot


func _profiled_validate_value(value: Variant) -> String:
	var started_usec := Time.get_ticks_usec()
	var problem := State.validate_value(value)
	_record_profile_duration("validate", started_usec)
	return problem


func _profiled_validate_snapshot(snapshot: Dictionary, build: String, owners: Array) -> String:
	var started_usec := Time.get_ticks_usec()
	var problem: String = State.validate_snapshot(snapshot, build, owners)
	_record_profile_duration("validate", started_usec)
	return problem


func _profiled_adapter_validate(adapter: RefCounted, snapshot: Dictionary) -> String:
	var started_usec := Time.get_ticks_usec()
	var problem: String = adapter.validate_state(snapshot)
	_record_profile_duration("validate", started_usec)
	return problem


func _profiled_load_state(snapshot: Dictionary) -> String:
	var rebuild_before := int(_adapter_profile_counters().get("rebuild_us", 0))
	var started_usec := Time.get_ticks_usec()
	var problem: String = _adapter.load_state(snapshot)
	var elapsed_usec := maxi(0, Time.get_ticks_usec() - started_usec)
	var rebuild_after := int(_adapter_profile_counters().get("rebuild_us", rebuild_before))
	profile.load_count += 1
	# Keep presentation reconstruction as its own cost so the simulator can
	# charge it separately from the adapter's state restore.
	profile.load_us += maxi(0, elapsed_usec - maxi(0, rebuild_after - rebuild_before))
	return problem


func _profiled_copy_dictionary(value: Dictionary, deep: bool) -> Dictionary:
	var started_usec := Time.get_ticks_usec()
	var result := value.duplicate(deep)
	_record_profile_duration("copy", started_usec)
	return result


func _record_profile_duration(kind: String, started_usec: int) -> void:
	var elapsed_usec := maxi(0, Time.get_ticks_usec() - started_usec)
	var count_key := kind + "_count"
	var time_key := kind + "_us"
	if profile.has(count_key) and profile.has(time_key):
		profile[count_key] = int(profile[count_key]) + 1
		profile[time_key] = int(profile[time_key]) + elapsed_usec


func _adapter_profile_counters() -> Dictionary:
	if _adapter == null or not _adapter.has_method("profile_counters"):
		return {}
	var value: Variant = _adapter.call("profile_counters")
	return value if value is Dictionary else {}


func _prune() -> void:
	if _adapter.has_method("confirm_through"):
		_adapter.confirm_through(mini(confirmed, frontier))
	# Never discard the state immediately before an unconfirmed input.
	var retain_from := mini(confirmed, maxi(0, frontier - _capacity + 1))
	if retain_from <= oldest_frame():
		return
	for slot in ["p1", "p2"]:
		_anchors[slot] = _profiled_copy_dictionary(_used[retain_from][slot], false)
		for frame in _actual[slot].keys():
			if frame <= retain_from:
				_actual[slot].erase(frame)
	for frame in _states.keys():
		if frame < retain_from:
			_states.erase(frame)
	for frame in _used.keys():
		if frame <= retain_from:
			_used.erase(frame)
	if _adapter.has_method("retain_states"):
		_adapter.retain_states(_states.values())


func sample_local(slot: String, sample_frame: int, held: Dictionary) -> Dictionary:
	if sample_frame != frontier + 1:
		return {"error": "Local input must be sampled once at the next simulation frame"}
	var target := sample_frame + _delay
	var problem := receive(epoch, slot, target, held)
	if not problem.is_empty(): return {"error": problem}
	return {"epoch": epoch, "slot": slot, "frame": target,
		"held": _profiled_copy_dictionary(held, false)}


static func _neutral() -> Dictionary:
	var neutral := {}
	for button in BUTTONS: neutral[button] = false
	return neutral
