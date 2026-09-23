extends RefCounted

# Deterministically derives timer deliveries from restored registrations and
# authoritative elapsed-time samples. Its wall-phase policy is intentionally
# explicit and is not a Flash callback-phase equivalence claim.
const State = preload("res://simulation_state.gd")
const COUNTDOWN_SPEC := "res://generated/main/timeout/timer.json"

var game: Node
var time_ms := -1
var countdown_due_ms := -1
var intro_due_ms := -1
var intro_sequence := 0
var nextfight_sequence := -1
var nextfight_due_ms := -1
var body_due_ms := {"p1": {}, "p2": {}}
var error := ""
var delivery_policy := "at-most-once-per-sample-per-interval; due callbacks run at their audited Main phase"


func configure(scene: Node, initial_time_ms: int) -> String:
	game = scene
	time_ms = initial_time_ms
	error = ""
	var countdown_spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(COUNTDOWN_SPEC))
	if game.countdown != null and game.countdown.recorded_active:
		countdown_due_ms = initial_time_ms + int(countdown_spec.interval_ms)
	else:
		countdown_due_ms = -1
	intro_due_ms = initial_time_ms + int(game.battle_intro.spec.poll_ms) if game.battle_intro.active and game.battle_intro.polling else -1
	intro_sequence = 0
	nextfight_sequence = int(game.ko_interval_sequence)
	nextfight_due_ms = -1
	body_due_ms = {"p1": {}, "p2": {}}
	return ""


func set_time(value: int) -> String:
	if value < time_ms:
		return "Online timer sample moved backward"
	time_ms = value
	return ""


func events_for_phase(phase: String, frame: int) -> Array:
	if game == null or time_ms < 0:
		return []
	match phase:
		"after_actor_advance":
			return _after_actor_events(frame)
		"before_root_observer":
			return _before_observer_events(frame)
	error = "Unsupported online timer phase: " + phase
	return []


func _after_actor_events(frame: int) -> Array:
	var events: Array = []
	_sync_source_timers()
	if game.countdown == null or not game.countdown.recorded_active:
		countdown_due_ms = -1
	if countdown_due_ms >= 0 and time_ms >= countdown_due_ms:
		events.append(_event("countdown", "after_actor_advance", frame, {"due_ms": countdown_due_ms}))
		countdown_due_ms = time_ms + _countdown_interval_ms()
	if intro_due_ms >= 0:
		if not game.battle_intro.active or not game.battle_intro.polling:
			intro_due_ms = -1
		elif time_ms >= intro_due_ms:
			intro_sequence += 1
			events.append(_event("intro_poll", "after_actor_advance", frame, {
				"sequence": intro_sequence, "time_ms": time_ms, "due_ms": intro_due_ms,
			}))
			intro_due_ms = time_ms + int(game.battle_intro.spec.poll_ms)
	_sync_body_timeouts()
	for slot in ["p1", "p2"]:
		var ids: Array = body_due_ms[slot].keys()
		ids.sort()
		for raw_id in ids:
			var id := int(raw_id)
			if int(body_due_ms[slot][raw_id]) <= time_ms:
				events.append(_event("body_timeout", "after_actor_advance", frame, {"slot": slot, "id": id, "due_ms": int(body_due_ms[slot][raw_id])}))
	events.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		if int(left.due_ms) != int(right.due_ms): return int(left.due_ms) < int(right.due_ms)
		var left_rank := _kind_rank(str(left.kind))
		var right_rank := _kind_rank(str(right.kind))
		if left_rank != right_rank: return left_rank < right_rank
		if left.kind == "body_timeout" and left.slot != right.slot: return left.slot == "p1"
		if left.kind == "body_timeout" and int(left.id) != int(right.id): return int(left.id) < int(right.id)
		return int(left.get("sequence", 0)) < int(right.get("sequence", 0))
	)
	return events


func _before_observer_events(frame: int) -> Array:
	var timer: Timer = game.ko_nextfight_timer
	if timer == null:
		nextfight_sequence = int(game.ko_interval_sequence)
		nextfight_due_ms = -1
		return []
	var sequence := int(game.ko_interval_sequence)
	if sequence != nextfight_sequence or nextfight_due_ms < 0:
		nextfight_sequence = sequence
		nextfight_due_ms = time_ms + int(round(timer.wait_time * 1000.0))
	if time_ms < nextfight_due_ms:
		return []
	var event := _event("nextfight", "before_root_observer", frame, {"due_ms": nextfight_due_ms})
	# A source interval is repeatable. Re-anchor at the delivered monotonic sample
	# to bound catch-up after a backgrounded tab or a mutually agreed pause.
	nextfight_due_ms = time_ms + int(round(timer.wait_time * 1000.0))
	return [event]


func _sync_body_timeouts() -> void:
	for slot in ["p1", "p2"]:
		var driver: Node = game.player_body_driver._driver if slot == "p1" else game.opponent_driver
		if driver == null or not driver.timeouts.recorded:
			error = "Online BODY timer requires recorded timeout mode"
			return
		var pending: Dictionary = driver.timeouts._pending
		for raw_id in body_due_ms[slot].keys():
			if not pending.has(int(raw_id)):
				body_due_ms[slot].erase(raw_id)
		for raw_id in pending.keys():
			var id := int(raw_id)
			if not body_due_ms[slot].has(str(id)):
				body_due_ms[slot][str(id)] = time_ms + int(pending[id].delay_ms)


func finish_frame() -> void:
	if game == null:
		return
	_sync_source_timers()
	_sync_body_timeouts()
	var timer: Timer = game.ko_nextfight_timer
	if timer == null:
		nextfight_sequence = int(game.ko_interval_sequence)
		nextfight_due_ms = -1
	elif int(game.ko_interval_sequence) != nextfight_sequence:
		nextfight_sequence = int(game.ko_interval_sequence)
		nextfight_due_ms = time_ms + int(round(timer.wait_time * 1000.0))


func _sync_source_timers() -> void:
	if game.countdown != null and game.countdown.recorded_active:
		if countdown_due_ms < 0:
			countdown_due_ms = time_ms + _countdown_interval_ms()
	else:
		countdown_due_ms = -1
	if game.battle_intro.active and game.battle_intro.polling:
		if intro_due_ms < 0:
			intro_due_ms = time_ms + int(game.battle_intro.spec.poll_ms)
	else:
		intro_due_ms = -1


func save_state(frame: int) -> Dictionary:
	return {"version": 1, "frame": frame, "time_ms": time_ms,
		"countdown_due_ms": countdown_due_ms, "intro_due_ms": intro_due_ms,
		"intro_sequence": intro_sequence, "nextfight_sequence": nextfight_sequence,
		"nextfight_due_ms": nextfight_due_ms, "body_due_ms": State.canonical(body_due_ms)}


func validate_state(snapshot: Variant, frame: int) -> String:
	if not snapshot is Dictionary or snapshot.get("version") != 1 or snapshot.get("frame") != frame:
		return "Invalid online timer state envelope"
	for field in ["time_ms", "countdown_due_ms", "intro_due_ms", "intro_sequence", "nextfight_sequence", "nextfight_due_ms"]:
		if not snapshot.get(field) is int:
			return "Invalid online timer field: " + field
	if snapshot.time_ms < 0 or snapshot.intro_sequence < 0 or snapshot.nextfight_sequence < -1:
		return "Invalid online timer coordinates"
	if not snapshot.get("body_due_ms") is Dictionary or snapshot.body_due_ms.keys().size() != 2:
		return "Invalid BODY deadline state"
	for slot in ["p1", "p2"]:
		if not snapshot.body_due_ms.get(slot) is Dictionary:
			return "Missing BODY deadline slot: " + slot
		for id in snapshot.body_due_ms[slot]:
			if not str(id).is_valid_int() or int(id) <= 0 or not snapshot.body_due_ms[slot][id] is int:
				return "Invalid BODY deadline"
	return State.validate_value(snapshot)


func load_state(snapshot: Dictionary) -> String:
	var problem := validate_state(snapshot, int(snapshot.get("frame", -1)))
	if not problem.is_empty(): return problem
	time_ms = snapshot.time_ms
	countdown_due_ms = snapshot.countdown_due_ms
	intro_due_ms = snapshot.intro_due_ms
	intro_sequence = snapshot.intro_sequence
	nextfight_sequence = snapshot.nextfight_sequence
	nextfight_due_ms = snapshot.nextfight_due_ms
	body_due_ms = snapshot.body_due_ms.duplicate(true)
	error = ""
	return ""


func _countdown_interval_ms() -> int:
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(COUNTDOWN_SPEC))
	return int(spec.interval_ms)


func _event(kind: String, phase: String, frame: int, details: Dictionary) -> Dictionary:
	var event := {"kind": kind, "phase": phase, "frame": frame}
	event.merge(details, true)
	return event


func _kind_rank(kind: String) -> int:
	match kind:
		"countdown": return 0
		"intro_poll": return 1
		"body_timeout": return 2
		"nextfight": return 3
		_: return 4
