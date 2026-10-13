extends SceneTree

# Training keeps both keyboards live (main.json frame_8 chushi). Losing
# canvas focus must not turn a released key into a permanent held input.
func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var surface = load("res://render_surface.tscn").instantiate()
	root.add_child(surface)
	surface.game.set_physics_process(false)
	var keyboard = load("res://keyboard_input_source.gd").new()
	for code in [KEY_L, KEY_KP_3]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = true
		Input.parse_input_event(event)
	Input.flush_buffered_events()
	assert(keyboard.fighter_input(surface.game.session, "p1").dash)
	assert(keyboard.fighter_input(surface.game.session, "p2").dash)
	root.focus_exited.emit()
	for player in ["p1", "p2"]:
		for held in keyboard.fighter_input(surface.game.session, player).values():
			assert(not held)
	# Focus recovery must still allow a fresh P2 keypress.
	var event := InputEventKey.new()
	event.keycode = KEY_KP_3
	event.physical_keycode = KEY_KP_3
	event.pressed = true
	Input.parse_input_event(event)
	Input.flush_buffered_events()
	assert(keyboard.fighter_input(surface.game.session, "p2").dash)
	root.focus_exited.emit()
	surface.queue_free()
	await process_frame
	print("INPUT_FOCUS_SMOKE_OK")
	quit()
