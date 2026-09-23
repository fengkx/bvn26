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


func configure(adapter: RefCounted, match_epoch: String, window: int, capacity: int, input_delay: int = 0) -> String:
	if _adapter != null:
		return "Session already configured"
	if match_epoch.is_empty() or window < 0 or input_delay < 0 or capacity < window + input_delay + 2:
		return "Invalid rollback history limits"
	for method in ["save_state", "validate_state", "load_state", "advance"]:
		if not adapter.has_method(method):
			return "Missing adapter method: " + method
	var snapshot: Dictionary = adapter.save_state()
	if not State.validate_value(snapshot).is_empty() or not snapshot.get("owners") is Dictionary:
		return "Adapter did not return owned value state"
	_build = snapshot.get("build", "")
	_owners = snapshot.owners.keys()
	var problem := State.validate_snapshot(snapshot, _build, _owners)
	if not problem.is_empty() or snapshot.get("frame") != 0:
		return "Invalid initial snapshot: " + problem
	problem = adapter.validate_state(snapshot)
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
	_states[0] = snapshot.duplicate(true)
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
	_actual[slot][frame] = held.duplicate(true)
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
	return _states.get(frame, {}).duplicate(true)


func oldest_frame() -> int:
	return int(_states.keys().min()) if not _states.is_empty() else 0


func can_receive_frame(frame: int) -> bool:
	return frame >= oldest_frame() + 1 and frame <= frontier + _capacity


func retained_bytes() -> int:
	return var_to_bytes([_states, _actual, _used, _anchors]).size()


static func validate_input(held: Dictionary) -> String:
	if held.size() != BUTTONS.size():
		return "Incomplete logical buttons"
	for button in BUTTONS:
		if not held.get(button) is bool:
			return "Invalid logical button: " + button
	return ""


func _input_for(slot: String, frame: int) -> Dictionary:
	if _actual[slot].has(frame):
		return _actual[slot][frame].duplicate()
	if _used.has(frame - 1):
		return _used[frame - 1][slot].duplicate()
	if not _anchors[slot].is_empty():
		return _anchors[slot].duplicate()
	return _neutral()


func _advance_one() -> String:
	var frame := frontier + 1
	var players := {"p1": _input_for("p1", frame), "p2": _input_for("p2", frame)}
	var problem: String = _adapter.advance(frame, players.duplicate(true))
	if not problem.is_empty():
		return problem
	var snapshot: Dictionary = _adapter.save_state()
	problem = State.validate_snapshot(snapshot, _build, _owners)
	if not problem.is_empty() or snapshot.frame != frame:
		return "Adapter produced invalid snapshot at %d: %s" % [frame, problem]
	problem = _adapter.validate_state(snapshot)
	if not problem.is_empty():
		return problem
	_used[frame] = players
	_states[frame] = snapshot.duplicate(true)
	frontier = frame
	return ""


func _correct(frame: int) -> String:
	if not _states.has(frame - 1):
		return "Missing pre-correction snapshot"
	var snapshot: Dictionary = _states[frame - 1].duplicate(true)
	var problem: String = _adapter.validate_state(snapshot)
	if not problem.is_empty():
		return problem
	problem = _adapter.load_state(snapshot)
	if not problem.is_empty():
		return problem
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


func _prune() -> void:
	if _adapter.has_method("confirm_through"):
		_adapter.confirm_through(mini(confirmed, frontier))
	# Never discard the state immediately before an unconfirmed input.
	var retain_from := mini(confirmed, maxi(0, frontier - _capacity + 1))
	if retain_from <= oldest_frame():
		return
	for slot in ["p1", "p2"]:
		_anchors[slot] = _used[retain_from][slot].duplicate()
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
	return {"epoch": epoch, "slot": slot, "frame": target, "held": held.duplicate()}


static func _neutral() -> Dictionary:
	var neutral := {}
	for button in BUTTONS: neutral[button] = false
	return neutral
