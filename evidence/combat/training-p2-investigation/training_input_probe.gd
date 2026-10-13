extends SceneTree
var game
func _initialize():
 run.call_deferred()
func key(code, pressed, physical = 0):
 var event = InputEventKey.new()
 event.keycode = code
 event.physical_keycode = physical if physical else code
 event.pressed = pressed
 Input.parse_input_event(event)
 Input.flush_buffered_events()
func settle():
 for tick in 700:
  game._advance_fight()
  if not game.battle_intro.active: break
func idle_check(name):
 for tick in 180: game._advance_fight()
 assert(not game.session.p2cpu)
 assert(not game.opponent_driver.controller.context.use_ai)
 assert(game.ichigo.ai_random_clock.registered_ms == -1)
 var x = game.ichigo.source_x
 for tick in 180: game._advance_fight()
 assert(is_equal_approx(x, game.ichigo.source_x), name)
 print('PASS ',name,' frame=',game.ichigo.current_source_frame(),' x=',x)
func run():
 game = load('res://main.tscn').instantiate()
 root.add_child(game)
 game.set_physics_process(false)
 game.recorded_training_timers = true
 game._replace_selected_actors(['鸣人','鼬'],['我爱罗','魂'])
 game._enter_current_fight(4)
 settle()
 var keyboard = load('res://keyboard_input_source.gd').new()
 for slot in game.session.P1_SLOTS:
  var code = game.session.flash_to_key(game.session.codes[slot])
  key(code,true)
  for held in keyboard.fighter_input(game.session,'p2').values(): assert(not held)
  key(code,false)
 print('PASS default P1 bindings never activate P2')
 var joy = InputEventJoypadMotion.new()
 joy.device = 1
 joy.axis = JOY_AXIS_LEFT_X
 joy.axis_value = 0.9
 Input.parse_input_event(joy)
 var button = InputEventJoypadButton.new()
 button.device = 1
 button.button_index = JOY_BUTTON_A
 button.pressed = true
 Input.parse_input_event(button)
 var touch = InputEventScreenTouch.new()
 touch.pressed = true
 touch.position = Vector2(300,300)
 Input.parse_input_event(touch)
 Input.flush_buffered_events()
 for held in keyboard.fighter_input(game.session,'p2').values(): assert(not held)
 print('PASS gamepad/touch do not activate P2')
 key(KEY_KP_3,true)
 for tick in 3: game._advance_fight()
 key(KEY_KP_3,false)
 idle_check('Itachi single dash release')
 for code in [KEY_D,KEY_J,KEY_L]:
  key(code,true)
  for tick in 45: game._advance_fight()
  key(code,false)
 idle_check('P1 move attack dash')
 game._enter_current_fight(2)
 settle()
 await create_timer(1.1).timeout
 assert(game.ichigo.ai_random_clock.sample_count > 0)
 print('AI samples before switch ',game.ichigo.ai_random_clock.sample_count)
 for tick in 90: game._advance_fight()
 game._enter_current_fight(4)
 settle()
 idle_check('AI sampled then training')
 game._ko_nextfight()
 settle()
 idle_check('rematch')
 game._goto_character_selection(4)
 game._replace_selected_actors(['一护','鸣人'],['我爱罗','魂'])
 game._enter_current_fight(4)
 settle()
 key(KEY_KP_3,true)
 for tick in 3: game._advance_fight()
 key(KEY_KP_3,false)
 idle_check('reselect Naruto single dash release')
 game._goto_menu()
 game.queue_free()
 await process_frame
 print('TRAINING_INPUT_PROBE_OK')
 quit()
