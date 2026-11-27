extends RefCounted

# A delivery log, not a battle snapshot or a deterministic simulation tape.
# Read phases stay at the existing consumers; immediate controls are never queued live.
const FORMAT := "bvn-match-input"
const VERSION := 1
const BUTTONS := preload("res://keyboard_input_source.gd").BUTTONS

var source: Callable
var intro_source: Callable
var recording := false
var playback := false
var finished := false
var error := ""
var document: Dictionary = {}
var _cursor := 0
var _previous := {"p1": {}, "p2": {}}


func begin_recording(setup: Dictionary) -> void:
	recording = true
	playback = false
	finished = false
	error = ""
	_previous = {"p1": {}, "p2": {}}
	document = {"kind": "match-input", "format": FORMAT, "version": VERSION, "setup": setup.duplicate(true), "events": [], "complete": false}


func begin_playback(data: Variant) -> String:
	var problem := validate(data)
	if not problem.is_empty():
		return problem
	document = data.duplicate(true)
	recording = false
	playback = true
	finished = false
	error = ""
	_cursor = 0
	return ""


func poll_intro(tick: int, keyboard: Callable) -> bool:
	if playback:
		var event := _expect("intro", tick)
		return bool(event.get("skip", false))
	var skip: bool = intro_source.call(tick) if intro_source.is_valid() else keyboard.call()
	if recording:
		document.events.append({"kind": "intro", "tick": tick, "skip": skip})
	return skip


func poll_players(tick: int, keyboard: Callable) -> Dictionary:
	if playback:
		var event := _expect("players", tick)
		if event.is_empty():
			return {}
		return {"p1": event.players.p1.held.duplicate(), "p2": event.players.p2.held.duplicate()}
	var inputs := {}
	for slot in ["p1", "p2"]:
		var raw: Dictionary = source.call(slot, tick) if source.is_valid() else keyboard.call(slot)
		var held := {}
		for button in BUTTONS:
			held[button] = bool(raw.get(button, false))
		inputs[slot] = held
	if recording:
		var samples := {}
		for slot in inputs:
			var held: Dictionary = inputs[slot].duplicate()
			var pressed := {}
			var released := {}
			for button in BUTTONS:
				var prior: bool = _previous[slot].get(button, false)
				pressed[button] = held[button] and not prior
				released[button] = not held[button] and prior
			samples[slot] = {"held": held, "pressed": pressed, "released": released}
			_previous[slot] = held
		document.events.append({"kind": "players", "tick": tick, "players": samples})
	return inputs


func record_control(tick: int, control: Dictionary) -> void:
	if recording:
		document.events.append({"kind": "control", "tick": tick, "control": control.duplicate(true)})


func take_controls(tick: int) -> Array:
	var result := []
	if not playback or finished or not error.is_empty():
		return result
	while _cursor < document.events.size():
		var event: Dictionary = document.events[_cursor]
		if event.kind != "control":
			break
		if int(event.tick) != tick:
			error = "Control tick mismatch at event %d" % _cursor
			break
		_cursor += 1
		result.append(event.control.duplicate(true))
	return result


func finish(tick: int, reason: String) -> void:
	if finished:
		return
	if playback:
		var event := _expect("end", tick)
		if event.get("reason", "") != reason:
			error = "Unexpected match exit: " + reason
	elif recording:
		document.events.append({"kind": "end", "tick": tick, "reason": reason})
		document.complete = true
	finished = true
	recording = false


func _expect(kind: String, tick: int) -> Dictionary:
	if not error.is_empty():
		return {}
	if finished or _cursor >= document.events.size():
		error = "Input exhausted at %s tick %d" % [kind, tick]
		return {}
	var event: Dictionary = document.events[_cursor]
	if event.kind != kind or int(event.tick) != tick:
		error = "Expected %s tick %d at event %d, got %s tick %s" % [kind, tick, _cursor, event.kind, event.tick]
		return {}
	_cursor += 1
	return event


static func valid_control(value: Variant) -> bool:
	if not value is Dictionary or not value.get("pressed") is bool:
		return false
	if value.get("button") not in ["confirm", "up", "down", "back"]:
		return false
	return value.button != "back" or value.get("inside") is bool


static func validate(data: Variant) -> String:
	if not data is Dictionary or data.get("kind") != "match-input" or data.get("format") != FORMAT or data.get("version") != VERSION:
		return "Unsupported input recording format/version"
	if data.get("complete") != true or not data.get("setup") is Dictionary or not data.get("events") is Array:
		return "Incomplete input recording"
	var start: Variant = data.setup.get("start_tick")
	if not (start is int or start is float) or not is_finite(float(start)) or start != int(start) or start < 0:
		return "Missing starting display tick"
	var tick := int(start)
	var phase := "intro"
	var previous := {"p1": {}, "p2": {}}
	var ended := false
	for event in data.events:
		if ended or not event is Dictionary or not (event.get("tick") is int or event.get("tick") is float):
			return "Malformed event or data after end"
		if not is_finite(float(event.tick)) or event.tick != int(event.tick):
			return "Non-integral event tick"
		match event.get("kind"):
			"intro":
				if phase != "intro" or int(event.tick) != tick + 1 or not event.get("skip") is bool:
					return "Missing, duplicate or invalid intro sample"
				tick += 1
				phase = "players"
			"players":
				if phase != "players" or int(event.tick) != tick or not event.get("players") is Dictionary:
					return "Missing, duplicate or invalid player sample"
				for slot in ["p1", "p2"]:
					var sample: Variant = event.players.get(slot)
					if not sample is Dictionary:
						return "Missing player slot"
					for field in ["held", "pressed", "released"]:
						if not sample.get(field) is Dictionary or sample[field].size() != BUTTONS.size():
							return "Incomplete logical buttons"
						for button in BUTTONS:
							if not sample[field].get(button) is bool:
								return "Invalid logical button"
					for button in BUTTONS:
						var prior: bool = previous[slot].get(button, false)
						if sample.pressed[button] != (sample.held[button] and not prior) or sample.released[button] != (not sample.held[button] and prior):
							return "Inconsistent button edges"
					previous[slot] = sample.held
				phase = "intro"
			"control":
				if phase != "intro" or int(event.tick) != tick or not valid_control(event.get("control")):
					return "Invalid control event phase/payload"
			"end":
				if phase != "intro" or int(event.tick) != tick or event.get("reason") not in ["title", "selection"]:
					return "Invalid match end"
				ended = true
			_:
				return "Unknown input event"
	return "" if ended else "Missing explicit match end"
