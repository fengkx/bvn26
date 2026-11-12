extends RefCounted

const Inputs = preload("res://rollback_session.gd")
const CAPACITY := 4
const STALE_MS := 250
var pending: Array[Dictionary] = []
var newest_sequence := 0
var consumed_sequence := 0
var last_received_ms := -1
var expired := 0
var seen := {}
var retired_ranges: Array = []
var held: Dictionary = neutral()

static func neutral() -> Dictionary:
	var result := {}
	for button in Inputs.BUTTONS: result[button] = false
	return result

func receive(sequence: int, buttons: Dictionary, now_ms: int) -> String:
	if sequence <= 0 or not Inputs.validate_input(buttons).is_empty():
		return "invalid_authority_input"
	if seen.has(sequence):
		return "" if seen[sequence] == buttons else "conflicting_authority_input"
	if sequence <= consumed_sequence: return ""
	seen[sequence] = buttons.duplicate()
	for old in seen.keys():
		if old < sequence - 64: seen.erase(old)
	if sequence > newest_sequence:
		newest_sequence = sequence
		last_received_ms = now_ms
	pending.append({"sequence": sequence, "held": buttons.duplicate(), "received_ms": now_ms})
	pending.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.sequence < b.sequence)
	if pending.size() > CAPACITY:
		var latest: Dictionary = pending.back()
		_retire(consumed_sequence + 1, int(latest.sequence) - 1)
		pending.assign([latest])
	return ""

func consume(now_ms: int) -> Dictionary:
	if last_received_ms < 0 or now_ms - last_received_ms > STALE_MS:
		_retire(consumed_sequence + 1, newest_sequence)
		pending.clear()
		held = neutral()
		return held.duplicate()
	if not pending.is_empty():
		# Never combine edges from different samples into an invented key chord.
		var first: Dictionary = pending.front()
		if int(first.sequence) > consumed_sequence + 1 and now_ms - int(first.received_ms) < 34:
			return held.duplicate()
		var next: Dictionary = pending.pop_front()
		_retire(consumed_sequence + 1, int(next.sequence) - 1)
		held = next.held.duplicate()
		consumed_sequence = int(next.sequence)
	return held.duplicate()

func reset() -> void:
	_retire(consumed_sequence + 1, newest_sequence)
	pending.clear()
	held = neutral()
	last_received_ms = -1

func _retire(first: int, last: int) -> void:
	if last < first: return
	expired += last - first + 1
	consumed_sequence = last
	retired_ranges.append([first, last])
	if retired_ranges.size() > 64: retired_ranges.pop_front()
