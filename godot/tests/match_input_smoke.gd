extends SceneTree

const Boundary = preload("res://match_input.gd")
var held := {"p1": {}, "p2": {}}

func _initialize() -> void:
	_run.call_deferred()


func _key(code: Key, pressed: bool) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = pressed
	Input.parse_input_event(event)
	Input.flush_buffered_events()


func _run() -> void:
	var session := GameSession.new()
	session.bind_slot("j", 81)
	_key(KEY_Q, true)
	_key(KEY_A, true)
	_key(KEY_D, true)
	_key(KEY_KP_2, true)
	var local := session.fighter_input("p1")
	assert(local.attack and local.left and local.right)
	assert(session.fighter_input("p2").jump)
	var recorder := Boundary.new()
	recorder.begin_recording({"start_tick": 0})
	assert(recorder.poll_intro(1, func() -> bool: return session.is_slot_down("j")))
	var first := recorder.poll_players(1, session.fighter_input)
	first.p1.attack = false
	assert(recorder.document.events[1].players.p1.held.attack)
	first.p1.attack = true
	for code in [KEY_Q, KEY_A, KEY_D, KEY_KP_2]: _key(code, false)
	recorder.record_control(1, {"button": "confirm", "pressed": true})
	recorder.record_control(1, {"button": "confirm", "pressed": false})
	assert(not recorder.poll_intro(2, func() -> bool: return false))
	var second := recorder.poll_players(2, session.fighter_input)
	recorder.finish(2, "title")
	var data: Dictionary = JSON.parse_string(JSON.stringify(recorder.document))
	assert(Boundary.validate(data).is_empty())
	var replay := Boundary.new()
	assert(replay.begin_playback(data).is_empty())
	_key(KEY_J, true)
	_key(KEY_KP_6, true)
	var forbidden := func(_slot: String) -> Dictionary:
		assert(false, "Playback sampled a local device")
		return {}
	assert(replay.poll_intro(1, func() -> bool: assert(false); return false))
	assert(replay.poll_players(1, forbidden) == first)
	assert(replay.take_controls(1) == [
		{"button": "confirm", "pressed": true}, {"button": "confirm", "pressed": false}])
	assert(not replay.poll_intro(2, func() -> bool: assert(false); return true))
	assert(replay.poll_players(2, forbidden) == second)
	replay.finish(2, "title")
	assert(replay.finished and replay.error.is_empty())
	assert(Input.is_key_pressed(KEY_J) and Input.is_key_pressed(KEY_KP_6))
	for code in [KEY_J, KEY_KP_6]: _key(code, false)
	var bad := data.duplicate(true)
	bad.events.remove_at(1)
	assert(not Boundary.validate(bad).is_empty())
	bad = data.duplicate(true)
	bad.events[1].players.p2.held.erase("jump")
	assert(not Boundary.validate(bad).is_empty())
	bad = data.duplicate(true)
	bad.events[1].players.p1.pressed.attack = false
	assert(not Boundary.validate(bad).is_empty())
	bad = data.duplicate(true)
	bad.complete = false
	assert(not Boundary.validate(bad).is_empty())
	bad = data.duplicate(true)
	bad.events.pop_back()
	assert(not Boundary.validate(bad).is_empty())
	bad = data.duplicate(true)
	bad.version = 99
	assert(not Boundary.validate(bad).is_empty())
	assert(replay.begin_playback(data).is_empty())
	replay.poll_intro(2, func() -> bool: return true)
	assert(not replay.error.is_empty())
	print("MATCH_INPUT_SMOKE_OK")
	quit()
