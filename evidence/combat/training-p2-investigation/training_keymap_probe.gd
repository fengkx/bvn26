extends SceneTree
func _initialize():
 run.call_deferred()
func run():
 var session = load('res://game_session.gd').new()
 var keyboard = load('res://keyboard_input_source.gd').new()
 session.codes = session.DEFAULT_CODES.duplicate()
 var event = InputEventKey.new()
 event.keycode = KEY_J
 event.physical_keycode = KEY_J
 event.pressed = true
 Input.parse_input_event(event)
 Input.flush_buffered_events()
 assert(not keyboard.fighter_input(session,'p2').dash)
 session.codes['N3'] = session.codes['j']
 assert(keyboard.fighter_input(session,'p1').attack and keyboard.fighter_input(session,'p2').dash)
 event = event.duplicate()
 event.pressed = false
 Input.parse_input_event(event)
 Input.flush_buffered_events()
 assert(not keyboard.fighter_input(session,'p2').dash)
 print('CUSTOM_OVERLAP_REQUIRES_KEYPRESS_OK')
 session.codes = session.DEFAULT_CODES.duplicate()
 event = InputEventKey.new()
 event.keycode = KEY_NONE
 event.physical_keycode = KEY_NONE
 event.unicode = 0x4e2d
 event.pressed = true
 Input.parse_input_event(event)
 Input.flush_buffered_events()
 for held in keyboard.fighter_input(session,'p2').values(): assert(not held)
 print('IME_TEXT_DOES_NOT_MAP_TO_P2_OK')
 quit()
