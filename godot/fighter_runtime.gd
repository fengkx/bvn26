class_name FighterRuntime
extends TimelinePreview

@export var display_depth: int = 1
@export var facing: int = 1

var fighter_name: String
var action: String = "站立"
var health: float = 1000.0
var energy: float = 300.0
var hitstun_ticks: int = 0
var timeline_playing: bool = true
var last_event: String = "ready"
var airborne: bool = false
var guarding: bool = false

var _combat: Dictionary
var _hit_instances: Dictionary = {}
var _ground_y: float
var _vertical_velocity: float = 0.0
var _double_jump_used: bool = false
var _guard_held: bool = false
var _dash_ticks: int = 0
var _dash_velocity: Vector2 = Vector2.ZERO
var _hurt_stop_applied: bool = false
var _hurt_motion_ticks: int = 0
var _hurt_horizontal_step: float = 0.0
var _hurt_vertical_step: float = 0.0
var _guard_horizontal_step: float = 0.0
var _jump_was_held: bool = false
var _jump_pressed: bool = false


func _ready() -> void:
	autoplay = false
	super._ready()
	_combat = _read_json("%s/combat.json" % fighter_directory)
	fighter_name = str(_combat.get("fighter_id", "fighter"))
	_ground_y = position.y
	set_facing(facing)
	start_action("站立")


func _physics_process(_delta: float) -> void:
	pass


func advance_timeline() -> void:
	if not timeline_playing:
		return
	if current_source_frame() >= int(action_range(action).get("end_frame", 0)):
		if action == "防御":
			start_action("防御2")
			return
		if action == "防住":
			start_action("防御2" if _guard_held else "站立")
			return
		if _is_one_shot_action(action):
			_finish_action()
			return
	advance_source_frame(true)


func enter_frame(input_state: Dictionary) -> void:
	var jump_held := bool(input_state.get("jump", false))
	_jump_pressed = jump_held and not _jump_was_held
	_jump_was_held = jump_held
	if health > 0.0 and health < 200.0:
		energy = minf(300.0, energy + 0.2)
	_guard_held = bool(input_state.get("down", false))
	guarding = action in ["防御", "防御2", "防住"] and _guard_held
	_run_source_motion()
	if _update_dash_motion():
		return
	if _update_air_motion(input_state):
		return
	if action == "被打":
		_update_hurt_motion()
		if not timeline_playing:
			hitstun_ticks = maxi(0, hitstun_ticks - 1)
			if hitstun_ticks == 0:
				timeline_playing = true
		return

	if action in ["砍1", "砍2"] and bool(input_state.get("attack", false)):
		for transition: Dictionary in _combat["combo"]["transitions"]:
			if transition["from"] == action and _frame_in(transition):
				start_action(str(transition["to"]))
				return

	if action == "防御2":
		if not _guard_held:
			start_action("站立")
		else:
			# The source clip calls gotoAndPlay("防御2") every enterFrame,
			# pinning a held guard to its first frame instead of looping it.
			play_action("防御2")
		return
	if action not in ["站立", "走"]:
		return

	var up := bool(input_state.get("up", false))
	var down := bool(input_state.get("down", false))
	if bool(input_state.get("special", false)):
		var special_label := "上必杀" if up else ("超必杀" if down else str(_combat["special"]["entry_label"]))
		var special_cost := 300.0 if down else 100.0
		if energy >= special_cost and _try_start_action(special_label):
			energy -= special_cost
		return
	if bool(input_state.get("summon", false)):
		if energy >= 100.0 and _try_start_action("招换"):
			energy -= 100.0
		return
	if bool(input_state.get("ranged", false)):
		_try_start_action("招3" if up else ("招2" if down else "招1"))
		return
	if bool(input_state.get("attack", false)):
		_try_start_action("砍技2" if up else ("砍技1" if down else "砍1"))
		return
	if bool(input_state.get("dash", false)):
		_start_dash(up, down)
		return
	if _jump_pressed:
		_start_jump(false)
		return
	if down:
		_try_start_action("防御")
		return

	var direction := int(input_state.get("right", false)) - int(input_state.get("left", false))
	if direction == 0:
		if action != "站立":
			start_action("站立")
		return
	position.x = clampf(
		position.x + direction * float(_combat["movement"]["speed_per_tick"]),
		20.0,
		580.0
	)
	set_facing(direction)
	if action != "走":
		start_action("走")


func run_frame_actions() -> void:
	if (
		action == "被打"
		and not _hurt_stop_applied
		and current_source_frame() == int(_combat["hurt"]["stop_frame"])
	):
		timeline_playing = false
		_hurt_stop_applied = true
		last_event = "hurt_stop"
		return
	if _combat["action_exits"].has(action):
		var exit: Dictionary = _combat["action_exits"][action]
		if current_source_frame() == int(exit["frame"]):
			start_action(str(exit["target"]))
			return
	if action == "必杀":
		for transition: Dictionary in _combat["special"]["transitions"]:
			if transition["from"] != action:
				continue
			if int(transition.get("frame", -1)) != current_source_frame():
				continue
			if (
				transition.get("condition") == "always"
				or (
					transition.get("condition") == "source_condition"
					and not _hit_instances.is_empty()
				)
			):
				start_action(str(transition["to"]))
				return


func receive_attack(attack: Dictionary, attacker_facing: int) -> void:
	var damage := float(attack["damage"])
	if guarding:
		health = maxf(0.0, health - damage / 10.0)
		energy = minf(300.0, energy + damage / 15.0)
		_guard_horizontal_step = attacker_facing * float(attack["horizontal_impulse"])
		start_action("防住")
		last_event = "guard_%s" % attack.get("instance_name", "unknown")
		print("COMBAT_EVENT ", JSON.stringify(snapshot()))
		return
	health = maxf(0.0, health - damage)
	energy = minf(300.0, energy + damage / 10.0)
	_hurt_motion_ticks = 0
	_hurt_horizontal_step = attacker_facing * float(attack["horizontal_impulse"])
	_hurt_vertical_step = -float(attack.get("vertical_impulse", 0.0))
	hitstun_ticks = ceili(float(attack["hitstun_ms"]) / 1000.0 * 30.0)
	start_action("被打")
	last_event = "hit_%s" % attack.get("instance_name", "unknown")
	print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func incoming_attack_hits(attacker: FighterRuntime) -> bool:
	var active := attacker.active_attack()
	if active.is_empty():
		return false
	var body := instance_global_bounds("bdmn")
	var attack_bounds := attacker.instance_global_bounds(str(active["instance_name"]))
	if not body.has_area() or not attack_bounds.has_area() or not body.intersects(attack_bounds):
		return false
	receive_attack(active, attacker.facing)
	attacker.mark_attack_hit(str(active["instance_name"]))
	if not attacker._is_special_action(attacker.action):
		attacker.energy = minf(300.0, attacker.energy + float(active["damage"]) / 5.0)
	return true


func active_attack() -> Dictionary:
	for window: Dictionary in _combat["hitbox_windows"].get(action, []):
		var instance_name := str(window["instance_name"])
		if _hit_instances.has(instance_name) or not _frame_in(window):
			continue
		var attack_key := instance_name.trim_suffix("atm")
		# AS2 authors sometimes suffixed duplicate instance names with zero
		# (for example zh20atm), while the attack table keeps the semantic key
		# (zh2). Resolve that source naming convention without weakening misses.
		if not _combat["attacks"].has(attack_key) and attack_key.ends_with("0"):
			attack_key = attack_key.trim_suffix("0")
		if not _combat["attacks"].has(attack_key):
			continue
		var result: Dictionary = _combat["attacks"][attack_key].duplicate(true)
		result["instance_name"] = instance_name
		return result
	return {}


func mark_attack_hit(instance_name: String) -> void:
	_hit_instances[instance_name] = true


func start_action(label: String) -> void:
	var frames := action_range(label)
	if frames.is_empty():
		push_error("Missing source action for %s: %s" % [fighter_name, label])
		return
	action = label
	guarding = label in ["防御", "防御2", "防住"] and _guard_held
	if label != "防住":
		_guard_horizontal_step = 0.0
	if label == "被打":
		_hurt_stop_applied = false
	timeline_playing = true
	_hit_instances.clear()
	play_action(label)
	last_event = "action_%s" % label
	print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func _try_start_action(label: String) -> bool:
	if action_range(label).is_empty():
		return false
	start_action(label)
	return true


func _start_jump(second_jump: bool) -> void:
	if airborne and (not second_jump or _double_jump_used):
		return
	if airborne:
		_double_jump_used = true
	else:
		airborne = true
		_double_jump_used = false
	_vertical_velocity = float(_fighter["movement_constants"]["jump_power"])
	start_action("跳2" if second_jump else "跳")


func _update_air_motion(input_state: Dictionary) -> bool:
	if not airborne:
		return false
	var direction := int(input_state.get("right", false)) - int(input_state.get("left", false))
	if direction != 0:
		position.x = clampf(
			position.x + direction * float(_combat["movement"]["speed_per_tick"]),
			20.0,
			580.0
		)
		set_facing(direction)
	if bool(input_state.get("down", false)) and bool(input_state.get("jump", false)):
		_vertical_velocity = minf(_vertical_velocity, -10.0)
	elif (
		_jump_pressed
		and not _double_jump_used
		and action == "跳"
		and current_source_frame() >= 50
	):
		_start_jump(true)
		return true
	if action in ["跳", "跳2", "落", "落2"]:
		if bool(input_state.get("special", false)) and energy >= 100.0:
			var air_special := "空中必杀"
			if _try_start_action(air_special):
				energy -= 100.0
		elif bool(input_state.get("ranged", false)):
			_try_start_action("跳招")
		elif bool(input_state.get("attack", false)):
			_try_start_action("跳砍")
	position.y -= _vertical_velocity
	_vertical_velocity -= 1.0
	if position.y >= _ground_y and _vertical_velocity <= 0.0:
		position.y = _ground_y
		_vertical_velocity = 0.0
		airborne = false
		start_action("落地")
		return true
	if _vertical_velocity <= 0.0 and action in ["跳", "跳2"]:
		start_action("落2" if _double_jump_used else "落")
	return true


func _start_dash(up: bool, down: bool) -> void:
	if up or down:
		if energy < 100.0:
			return
		energy -= 100.0
		_dash_ticks = 9
		_dash_velocity = Vector2(0.0, -14.0 if up else 12.0)
		airborne = true
		start_action("落")
		return
	_dash_ticks = 11
	_dash_velocity = Vector2(float(_combat["movement"]["speed_per_tick"]) * 2.5 * facing, 0.0)
	start_action("瞬步")


func _update_dash_motion() -> bool:
	if _dash_ticks <= 0:
		return false
	position += _dash_velocity
	position.x = clampf(position.x, 20.0, 580.0)
	_dash_ticks -= 1
	if _dash_ticks == 0:
		if _dash_velocity.y != 0.0:
			_vertical_velocity = -_dash_velocity.y
			start_action("落2")
		else:
			start_action("站立")
	return true


func _finish_action() -> void:
	if airborne:
		start_action("落2" if _double_jump_used else "落")
	else:
		start_action("站立")


func _run_source_motion() -> void:
	var frame := current_source_frame()
	var speed := float(_combat["movement"]["speed_per_tick"])
	if fighter_name == "鸣人":
		if action == "砍1" and frame >= 172 and frame <= 175:
			_move_forward(roundf(speed / 4.0))
		elif action == "砍2" and frame >= 190 and frame <= 196:
			_move_forward(roundf(speed / 2.0))
		elif action == "砍3" and frame >= 211 and frame <= 216:
			_move_forward(roundf(speed * 1.3))
		elif action == "砍4" and frame >= 238 and frame <= 245:
			_move_forward(roundf(speed))
		elif action == "砍技1" and frame >= 273 and frame <= 290:
			if _hit_instances.is_empty():
				_move_forward(speed * 2.0)
			else:
				_try_start_action("砍技12")
		elif action == "砍技2" and frame >= 327 and frame <= 332:
			_move_forward(roundf(speed))
		elif action == "砍技2" and frame >= 333 and frame <= 345:
			_move_forward(3.0)
		elif action == "招3" and frame >= 478 and frame <= 484:
			_move_forward(speed * 1.8)
			position.y -= speed * 2.4
		elif action == "招3" and frame >= 485 and frame <= 503:
			_move_forward(speed * 1.7)
		elif action == "必杀" and frame >= 530 and frame <= 539:
			_move_forward(roundf(speed))
	else:
		if action == "砍1" and frame >= 175 and frame <= 180:
			_move_forward(roundf(speed / 4.0))
		elif action == "砍2" and frame >= 192 and frame <= 197:
			_move_forward(roundf(speed / 3.0))
		elif action == "砍3" and frame >= 212 and frame <= 218:
			_move_forward(roundf(speed / 4.0))
		elif action == "招2" and frame >= 359 and frame <= 370:
			if _hit_instances.is_empty():
				_move_forward(speed * 3.0)
			else:
				_try_start_action("招21")
	if action == "防住" and _guard_horizontal_step != 0.0:
		_move_world_x(_guard_horizontal_step)


func _update_hurt_motion() -> void:
	# The source beidax() keeps applying hitx/yup while the hurt timeline is
	# stopped. A one-off impulse changes HP but is almost invisible on screen.
	if _hurt_motion_ticks <= 13:
		_move_world_x(_hurt_horizontal_step)
		position.y += _hurt_vertical_step
	_hurt_motion_ticks += 1


func _move_world_x(distance: float) -> void:
	position.x = clampf(position.x + distance, 20.0, 580.0)


func _move_forward(distance: float) -> void:
	_move_world_x(distance * facing)


func _is_special_action(label: String) -> bool:
	return label in ["必杀", "必杀1", "必杀0", "上必杀", "超必杀", "空中必杀"]


func _is_one_shot_action(label: String) -> bool:
	return label not in [
		"站立", "走", "跳", "跳2", "落", "落2", "防御", "防御2", "被打"
	]


func set_facing(value: int) -> void:
	if value == 0:
		return
	facing = signi(value)
	scale.x = absf(scale.x) * facing


func snapshot() -> Dictionary:
	return {
		"fighter": fighter_name,
		"action": action,
		"frame": current_source_frame(),
		"x": position.x,
		"facing": facing,
		"health": health,
		"energy": energy,
		"hitstun_ticks": hitstun_ticks,
		"timeline_playing": timeline_playing,
		"airborne": airborne,
		"guarding": guarding,
		"event": last_event,
	}


func _frame_in(window: Dictionary) -> bool:
	return (
		current_source_frame() >= int(window["start_frame"])
		and current_source_frame() <= int(window["end_frame"])
	)
