class_name FighterRuntime
extends TimelinePreview

signal hit_effect_requested(effect_name: String, source_position: Vector2, source_facing: int)
signal screen_flash_requested(color_rgb24: int)

@export var display_depth: int = 1
@export var facing: int = 1

var fighter_name: String
var action: String = "站立"
var health: float = 1000.0
var energy: float = 0.0
var hitstun_ticks: int = 0
var timeline_playing: bool = true
var last_event: String = "ready"
var airborne: bool = false
var guarding: bool = false
# Source player wrapper values used by mc.on_enterframe body pressure.
var body_heavy: float = 2.0
var body_forward_velocity: float = 0.0
# Source mc.sw from checkDead(); locks input and blocks 起身 / 站立.
var sw: bool = false
var player_slot: String = ""

var _combat: Dictionary
var _commands: CommandCatalog = CommandCatalog.new()
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
var _body_last_x: float = 0.0
var _jump_was_held: bool = false
var _jump_pressed: bool = false
var _stage_platforms: Array[Rect2] = []
var _wall_min: float = 20.0
var _wall_max: float = 970.0
var _hurt_falling: bool = false
var _launched: bool = false
var _zhongli_fall: bool = false
var _energy_event_applied: bool = false
var _summon_applied: bool = false
var _presentation_events_applied: Dictionary = {}
var helper_spawn: Dictionary = {}
var opponent: FighterRuntime
var last_hit_effect: String = ""


func _ready() -> void:
	autoplay = false
	super._ready()
	_combat = _read_json("%s/combat.json" % fighter_directory)
	_commands.load_combat(_combat)
	fighter_name = str(_combat.get("fighter_id", "fighter"))
	_ground_y = position.y
	set_facing(facing)
	start_action("站立")


func _physics_process(_delta: float) -> void:
	pass


func advance_timeline() -> void:
	if not timeline_playing:
		return
	if _should_stop_dead_knockdown():
		timeline_playing = false
		last_event = "death_stop"
		return
	if current_source_frame() >= int(action_range(action).get("end_frame", 0)):
		if action == "防御":
			start_action("防御2")
			return
		if action == "防住":
			start_action("防御2" if _guard_held else "站立")
			return
		if action in ["被打", "击飞"]:
			return
		if _is_one_shot_action(action):
			_finish_action()
			return
	advance_source_frame(true)


func enter_frame(input_state: Dictionary) -> void:
	if _combat_input_locked():
		input_state = {}
	var jump_held := bool(input_state.get("jump", false))
	_jump_pressed = jump_held and not _jump_was_held
	_jump_was_held = jump_held
	if health > 0.0 and health < 200.0:
		change_energy(0.2)
	_guard_held = bool(input_state.get("down", false))
	guarding = action in ["防御", "防御2", "防住"] and _guard_held
	# Source frame DoAction (gotoAndStop) runs when the playhead enters the
	# frame, before that frame's clip enterFrame motion.
	_apply_action_exit()
	_run_source_motion()
	if _update_dash_motion():
		return
	if not _uses_scripted_flight() and _update_air_motion(input_state):
		return
	if _is_hurt_action(action):
		_update_hurt_motion()
		if action == "被打" and not timeline_playing:
			hitstun_ticks = maxi(0, hitstun_ticks - 1)
			if hitstun_ticks == 0:
				timeline_playing = true
		return
	if _update_hurt_fall():
		return
	# DefineSprite_16 enterFrame keeps calling doDropDown() while that clip
	# stays on the display list, including 防御2. jumpDown() is only blocked
	# when touchFloor is true (main floor), not while standing on a ban.
	if _jump_pressed and _guard_held:
		if _start_drop_through():
			return
	if not airborne:
		var stand_y := _hit_ban_y(position)
		if not is_nan(stand_y):
			position.y = stand_y
	if (
		not _uses_scripted_flight()
		and position.y < _ground_y
		and not _has_support_at(position)
	):
		airborne = true
		_vertical_velocity = 0.0
		_zhongli_fall = true
		start_action("落")
		_update_air_motion(input_state)
		return

	if action in ["砍1", "砍2"] and bool(input_state.get("attack", false)):
		for transition: Dictionary in _combat["combo"]["transitions"]:
			if transition["from"] == action and _frame_in(transition):
				start_action(str(transition["to"]))
				return

	# Guard and stand buttons come from the shared command catalog
	# (doAllAction / onDefence predicates). New fighters only need their
	# combat.json slots; directional specials win by dispatch_priority.
	if action in ["防御", "防御2"]:
		if _dispatch_catalog("guard", input_state):
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
	if _dispatch_catalog("stand", input_state):
		return

	var direction := int(input_state.get("right", false)) - int(input_state.get("left", false))
	if direction == 0:
		if action != "站立":
			start_action("站立")
		return
	_move_world_x(direction * float(_combat["movement"]["speed_per_tick"]))
	set_facing(direction)
	if action != "走":
		start_action("走")


func run_frame_actions() -> void:
	_apply_source_energy_event()
	_apply_summon_event()
	_apply_presentation_events()
	if (
		action == "被打"
		and not _hurt_stop_applied
		and current_source_frame() == int(_combat["hurt"]["stop_frame"])
	):
		timeline_playing = false
		_hurt_stop_applied = true
		last_event = "hurt_stop"
		return
	if _should_stop_dead_knockdown():
		timeline_playing = false
		last_event = "death_stop"
		return
	if _apply_action_exit():
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
	var impact_strength := int(attack.get("impact_strength", 0))
	# Source fangyu() treats zl > 10 as a guard break, then removes the
	# encoding offset before choosing the normal hit presentation.
	var guard_broken := guarding and impact_strength > 10
	if guarding and not guard_broken:
		health = maxf(0.0, health - damage / 10.0)
		change_energy(damage / 15.0)
		_guard_horizontal_step = attacker_facing * float(attack["horizontal_impulse"])
		start_action("防住")
		last_event = "guard_%s" % attack.get("instance_name", "unknown")
		# Source onDefence() ends with checkDead(false).
		_check_dead(false)
		print("COMBAT_EVENT ", JSON.stringify(snapshot()))
		return
	last_hit_effect = _hit_effect_for_strength(impact_strength)
	if last_hit_effect != "":
		hit_effect_requested.emit(last_hit_effect, position, facing)
	health = maxf(0.0, health - damage)
	change_energy(damage / 10.0)
	_hurt_motion_ticks = 0
	_hurt_horizontal_step = attacker_facing * float(attack["horizontal_impulse"])
	_hurt_vertical_step = -float(attack.get("vertical_impulse", 0.0))
	var reaction := str(attack.get("reaction_label", "被打"))
	var flying := reaction == _death_launch_label()
	_launched = flying
	_hurt_falling = _launched or _hurt_vertical_step != 0.0 or position.y < _ground_y
	hitstun_ticks = ceili(float(attack["hitstun_ms"]) / 1000.0 * 30.0)
	if not _try_start_action(reaction):
		start_action("被打")
	last_event = "hit_%s" % attack.get("instance_name", "unknown")
	# Source onBeHit() calls checkDead(flying) after hitlosehp().
	_check_dead(flying)
	print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func _hit_effect_for_strength(strength: int) -> String:
	# beida()/fangyu() remove the >10 guard-break marker before bdxg().
	var presentation_strength := strength - 10 if strength > 10 else strength
	match presentation_strength:
		1:
			return "XG_kan"
		2:
			return "XG_qdj"
		3:
			return "XG_qdjx"
		4:
			return "XG_mfdj"
		5:
			return "XG_mfdjx"
		6:
			return "XG_kanx"
	return ""


func incoming_attack_hits(attacker: FighterRuntime) -> bool:
	var contact := attacker.attack_contact(self)
	if contact.is_empty():
		return false
	attacker.apply_attack_contact(contact, self)
	return true


func sync_body_collision_position() -> void:
	_body_last_x = position.x
	body_forward_velocity = 0.0


func resolve_body_collision(other: FighterRuntime) -> void:
	# Source on_enterframe skips body pressure while doDashX owns movement.
	if _dash_ticks > 0:
		sync_body_collision_position()
		return
	var movement := clampf(position.x - _body_last_x, -30.0, 30.0)
	var forward_pressure := movement * float(facing)
	if forward_pressure > 0.0:
		forward_pressure += other.body_forward_velocity / 2.0
		body_forward_velocity = forward_pressure
	else:
		body_forward_velocity = 0.0
	var body := instance_global_bounds("bdmn")
	var other_body := other.instance_global_bounds("bdmn")
	if (
		forward_pressure >= 0.0
		and body.has_area()
		and other_body.has_area()
		and body.intersects(other_body)
	):
		# The original injects ten pixels of pressure when two idle bodies are
		# already touching, so accidental overlap resolves instead of persisting.
		if forward_pressure == 0.0 and other.body_forward_velocity == 0.0:
			forward_pressure = 10.0
		var heavy_delta := maxf(0.0, other.body_heavy - body_heavy)
		var other_push := maxf(0.0, forward_pressure / 2.0 - heavy_delta)
		var self_push := forward_pressure - other_push
		other.position.x += other_push * float(facing)
		position.x -= self_push * float(facing)
	_body_last_x = position.x


func attack_contact(defender: FighterRuntime) -> Dictionary:
	var body := defender.instance_global_bounds("bdmn")
	if not body.has_area():
		return {}
	for instance_name in _ordered_attack_instances():
		if not instance_name.ends_with("atm") or _hit_instances.has(instance_name):
			continue
		var attack := _attack_from_instance(instance_name)
		if attack.is_empty():
			continue
		var attack_bounds := instance_global_bounds(instance_name)
		if attack_bounds.has_area() and body.intersects(attack_bounds):
			return attack
	return {}


func _ordered_attack_instances() -> PackedStringArray:
	var visible: Dictionary = {}
	for instance_name in current_named_instances():
		if str(instance_name).ends_with("atm"):
			visible[str(instance_name)] = true
	var ordered := PackedStringArray()
	for instance_name in _combat.get("hit_priority", {}).get("instances", []):
		var name := str(instance_name)
		if visible.erase(name):
			ordered.append(name)
	# Unknown source names remain usable, but never displace a sourced priority.
	var remaining := PackedStringArray(visible.keys())
	remaining.sort()
	ordered.append_array(remaining)
	return ordered


func apply_attack_contact(attack: Dictionary, defender: FighterRuntime) -> void:
	var action_was_special := _is_special_action(action)
	var was_guarded := (
		defender.guarding and int(attack.get("impact_strength", 0)) <= 10
	)
	defender.receive_attack(attack, facing)
	mark_attack_hit(str(attack["instance_name"]))
	if not action_was_special:
		change_energy(float(attack["damage"]) / (10.0 if was_guarded else 5.0))


func active_attack() -> Dictionary:
	for instance_name in current_named_instances():
		if not instance_name.ends_with("atm") or _hit_instances.has(instance_name):
			continue
		var attack := _attack_from_instance(instance_name)
		if not attack.is_empty() and instance_global_bounds(instance_name).has_area():
			return attack
	return {}


func _attack_from_instance(instance_name: String) -> Dictionary:
	var attack_key := instance_name.trim_suffix("atm")
	# AS2 authors sometimes suffixed duplicate instance names with zero
	# (for example zh20atm), while the attack table keeps the semantic key
	# (zh2). Resolve that source naming convention without weakening misses.
	if not _combat["attacks"].has(attack_key) and attack_key.ends_with("0"):
		attack_key = attack_key.trim_suffix("0")
	if not _combat["attacks"].has(attack_key):
		return {}
	var result: Dictionary = _combat["attacks"][attack_key].duplicate(true)
	result["instance_name"] = instance_name
	return result


func mark_attack_hit(instance_name: String) -> void:
	_hit_instances[instance_name] = true


func _apply_action_exit() -> bool:
	if not _combat["action_exits"].has(action):
		return false
	var exit: Dictionary = _combat["action_exits"][action]
	if current_source_frame() != int(exit["frame"]):
		return false
	var target := str(exit["target"])
	var leave_scripted_flight := _uses_scripted_flight()
	start_action(target)
	# 招3 sets jump=1 so on_enterframe skips zhongli; goto "落" then
	# 落 frame 56 does jump=0 and gravity is _root.zhongli.
	if leave_scripted_flight and target in ["落", "落2"]:
		airborne = true
		_zhongli_fall = true
		_vertical_velocity = 0.0
	return true


func start_action(label: String) -> void:
	if sw and not _is_death_sequence_action(label):
		return
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
	_energy_event_applied = false
	_summon_applied = false
	_presentation_events_applied.clear()
	# Keep helper_spawn until GameWorld consumes yfgj(). start_action("站立")
	# on the same tick must not drop doZhaoHuan's placement.
	timeline_playing = true
	_hit_instances.clear()
	play_action(label)
	last_event = "action_%s" % label
	print("COMBAT_EVENT ", JSON.stringify(snapshot()))


func _try_start_action(label: String) -> bool:
	if _combat_input_locked() and not _is_death_sequence_action(label):
		return false
	if action_range(label).is_empty():
		return false
	start_action(label)
	return true


func _dispatch_catalog(context: String, input_state: Dictionary) -> bool:
	var entry := _commands.match_context(context, input_state, energy, true)
	if entry.is_empty():
		return false
	var handler := str(entry.get("handler", "start_action"))
	var label := str(entry.get("label", ""))
	if handler == "start_jump":
		_start_jump(false)
		return true
	if handler == "start_dash":
		# rush() is 冲 and not 上/下; vertical L dashes were not sourced here.
		_start_dash(false, false)
		return true
	return _try_start_action(label)


func has_command(label: String) -> bool:
	return _commands.has_label(label)


func command_is_wired(label: String) -> bool:
	return _commands.is_wired(label)


func command_gaps() -> Array:
	return _commands.gaps()


func start_command(label: String) -> bool:
	# Public hook for later move work and extra fighters. Labels are the
	# original timeline IDs; catalog_only still plays if the span exists.
	return _try_start_action(label)


func _start_jump(second_jump: bool) -> void:
	if airborne and (not second_jump or _double_jump_used):
		return
	if airborne:
		_double_jump_used = true
	else:
		airborne = true
		_double_jump_used = false
	_zhongli_fall = false
	_vertical_velocity = float(_fighter["movement_constants"]["jump_power"])
	start_action("跳2" if second_jump else "跳")


func _start_drop_through() -> bool:
	# jumpDown() returns false only when touchFloor; doDropDown() then does
	# _y += _root.zhongli and gotoAndPlay("落2"). The +10 leaves the isHitBan
	# window (ban._y - 10, ban._y], so the next surface below is used.
	if _touch_floor():
		return false
	position.y += _zhongli()
	airborne = true
	_zhongli_fall = true
	_vertical_velocity = 0.0
	start_action("落2")
	return true


func _update_air_motion(input_state: Dictionary) -> bool:
	if not airborne:
		return false
	var direction := int(input_state.get("right", false)) - int(input_state.get("left", false))
	if direction != 0:
		_move_world_x(direction * float(_combat["movement"]["speed_per_tick"]))
		set_facing(direction)
	if (
		not _zhongli_fall
		and bool(input_state.get("down", false))
		and bool(input_state.get("jump", false))
	):
		_vertical_velocity = minf(_vertical_velocity, -_zhongli())
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
			_try_start_action(air_special)
		elif bool(input_state.get("ranged", false)):
			_try_start_action("跳招")
		elif bool(input_state.get("attack", false)):
			_try_start_action("跳砍")
	var previous_y := position.y
	if _zhongli_fall:
		position.y += _zhongli()
	else:
		position.y -= _vertical_velocity
		_vertical_velocity -= 1.0
	var landing_y := _landing_surface_y(previous_y, position.y)
	var falling := _zhongli_fall or _vertical_velocity <= 0.0
	if not is_nan(landing_y) and falling:
		position.y = landing_y
		_vertical_velocity = 0.0
		airborne = false
		_zhongli_fall = false
		start_action("落地")
		return true
	if not _zhongli_fall and _vertical_velocity <= 0.0 and action in ["跳", "跳2"]:
		start_action("落2" if _double_jump_used else "落")
	return true


func _start_dash(up: bool, down: bool) -> void:
	if up or down:
		if energy < 100.0:
			return
		change_energy(-100.0)
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
	position.x = clampf(position.x, _wall_min, _wall_max)
	_dash_ticks -= 1
	if _dash_ticks == 0:
		if _dash_velocity.y != 0.0:
			_vertical_velocity = -_dash_velocity.y
			start_action("落2")
		else:
			start_action("站立")
	return true


func _finish_action() -> void:
	if sw:
		# Source standup() and 击落地 sw-stop never leave death for 起身/站立.
		if action == _death_down_label():
			timeline_playing = false
			last_event = "death_stop"
		return
	if action == "击落地":
		start_action("起身")
		return
	if airborne or _hurt_falling:
		start_action("落2" if _double_jump_used else "落")
	else:
		start_action("站立")


func _run_source_motion() -> void:
	var frame := current_source_frame()
	var speed := float(_combat["movement"]["speed_per_tick"])
	for window: Dictionary in _combat.get("motion_windows", []):
		if str(window.get("action", "")) != action:
			continue
		if frame < int(window["start_frame"]) or frame > int(window["end_frame"]):
			continue
		if window.has("contact_cancel_to") and _motion_contact_hit(window):
			_try_start_action(str(window["contact_cancel_to"]))
			return
		if window.has("forward_speed_factor"):
			var distance := speed * float(window["forward_speed_factor"])
			if bool(window.get("round_forward", false)):
				distance = roundf(distance)
			if window.has("contact_cancel_to") and _sweep_motion_contact(window, distance):
				return
			_move_forward(distance)
		if window.has("forward_pixels"):
			_move_forward(float(window["forward_pixels"]))
		if window.has("vertical_speed_factor"):
			var previous_y := position.y
			var rise := speed * float(window["vertical_speed_factor"])
			if bool(window.get("round_vertical", false)):
				rise = roundf(rise)
			position.y += rise
			if window.has("land_cancel_to"):
				var landing_y := _landing_surface_y(previous_y, position.y)
				if not is_nan(landing_y):
					position.y = landing_y
					airborne = false
					_vertical_velocity = 0.0
					_try_start_action(str(window["land_cancel_to"]))
					return
		elif window.has("land_cancel_to") and _has_support_at(position):
			airborne = false
			_vertical_velocity = 0.0
			_try_start_action(str(window["land_cancel_to"]))
			return
	if action == "防住" and _guard_horizontal_step != 0.0:
		_move_world_x(_guard_horizontal_step)
	_update_projectiles()


func _uses_scripted_flight() -> bool:
	for window: Dictionary in _combat.get("motion_windows", []):
		if str(window.get("action", "")) != action:
			continue
		if window.has("vertical_speed_factor") or window.has("land_cancel_to"):
			return true
	return false


func _motion_contact_hit(window: Dictionary) -> bool:
	var instance_name := str(window.get("contact_instance", ""))
	if opponent != null and is_instance_valid(opponent):
		var body := opponent.instance_global_bounds("bdmn")
		if not body.has_area():
			return false
		if instance_name != "":
			var attack_bounds := instance_global_bounds(instance_name)
			return attack_bounds.has_area() and body.intersects(attack_bounds)
		return not attack_contact(opponent).is_empty()
	return instance_name != "" and _hit_instances.has(instance_name)


func _sweep_motion_contact(window: Dictionary, forward_distance: float) -> bool:
	if opponent == null or not is_instance_valid(opponent):
		return false
	var instance_name := str(window.get("contact_instance", ""))
	if instance_name == "":
		return false
	var attack_bounds := instance_global_bounds(instance_name)
	var body := opponent.instance_global_bounds("bdmn")
	if not attack_bounds.has_area() or not body.has_area():
		return false
	var delta_x := forward_distance * float(facing)
	var fraction := _horizontal_sweep_fraction(attack_bounds, body, delta_x)
	if fraction < 0.0:
		return false
	# The Flash clip tests before each speed*2 step. The swept fallback preserves
	# the first crossed contact when converted AABBs would otherwise tunnel.
	var contact_distance := absf(delta_x) * fraction
	_move_world_x(float(signf(delta_x)) * minf(absf(delta_x), contact_distance + 0.01))
	_try_start_action(str(window["contact_cancel_to"]))
	return true


func _horizontal_sweep_fraction(moving: Rect2, target: Rect2, delta_x: float) -> float:
	if is_zero_approx(delta_x):
		return -1.0
	if moving.end.y <= target.position.y or moving.position.y >= target.end.y:
		return -1.0
	var entry: float
	var leave: float
	if delta_x > 0.0:
		entry = (target.position.x - moving.end.x) / delta_x
		leave = (target.end.x - moving.position.x) / delta_x
	else:
		entry = (target.end.x - moving.position.x) / delta_x
		leave = (target.position.x - moving.end.x) / delta_x
	if entry > leave or leave < 0.0 or entry > 1.0:
		return -1.0
	return clampf(entry, 0.0, 1.0)


func _update_projectiles() -> void:
	var frame := current_source_frame()
	var speed := float(_combat["movement"]["speed_per_tick"])
	var live: Dictionary = {}
	var moved := false
	for projectile: Dictionary in _combat.get("projectiles", []):
		if str(projectile.get("action", "")) != action:
			continue
		if frame < int(projectile["start_frame"]) or frame > int(projectile["end_frame"]):
			continue
		var instance_name := str(projectile["instance_name"])
		live[instance_name] = true
		var existed := _instance_local_frames.has(instance_name)
		if not existed:
			_start_clip_playhead(instance_name, projectile)
			moved = true
		var jumped_hit := false
		if _projectile_blocked(instance_name):
			if projectile.has("on_hit_goto_frame") and not _clip_past_hit(
				instance_name, projectile
			):
				set_instance_clip_frame(
					instance_name, int(projectile["on_hit_goto_frame"]), true
				)
				jumped_hit = true
				moved = true
		else:
			var offset := instance_local_offset(instance_name)
			var step := speed * float(projectile.get("speed_factor", 1.0))
			offset.x += step * float(projectile.get("local_x_factor", 0.0))
			offset.y += step * float(projectile.get("local_y_factor", 0.0))
			set_instance_local_offset(instance_name, offset)
			moved = true
		if existed and not jumped_hit:
			_advance_clip_playhead(instance_name, projectile)
	for instance_name in _instance_local_offsets.keys():
		if not live.has(instance_name):
			_instance_local_offsets.erase(instance_name)
			_instance_local_frames.erase(instance_name)
			moved = true
	if moved:
		refresh_display()


func _start_clip_playhead(instance_name: String, projectile: Dictionary) -> void:
	set_instance_clip_frame(instance_name, 1, not _is_stop_frame(projectile, 1), 0)


func _advance_clip_playhead(instance_name: String, projectile: Dictionary) -> void:
	if not _instance_local_frames.has(instance_name):
		return
	var record: Dictionary = _instance_local_frames[instance_name]
	var current := int(record.get("local_start", 1))
	var age := int(record.get("age", 0)) + 1
	if not bool(record.get("playing", true)) or _is_stop_frame(projectile, current):
		set_instance_clip_frame(instance_name, current, false, age)
		return
	var next_frame := current + 1
	set_instance_clip_frame(
		instance_name, next_frame, not _is_stop_frame(projectile, next_frame), age
	)


func _is_stop_frame(projectile: Dictionary, frame: int) -> bool:
	for item in projectile.get("stop_frames", []):
		if int(item) == frame:
			return true
	return false


func _clip_past_hit(instance_name: String, projectile: Dictionary) -> bool:
	if not projectile.has("on_hit_goto_frame"):
		return false
	return instance_clip_frame(instance_name) >= int(projectile["on_hit_goto_frame"])


func _projectile_blocked(instance_name: String) -> bool:
	if _hit_instances.has(instance_name):
		return true
	if opponent == null or not is_instance_valid(opponent):
		return false
	var body := opponent.instance_global_bounds("bdmn")
	var attack_bounds := instance_global_bounds(instance_name)
	return body.has_area() and attack_bounds.has_area() and body.intersects(attack_bounds)


func _update_hurt_motion() -> void:
	# The source beidax() keeps applying hitx/yup while the hurt timeline is
	# stopped. A one-off impulse changes HP but is almost invisible on screen.
	if _hurt_motion_ticks <= 13:
		_move_world_x(_hurt_horizontal_step)
		position.y += _hurt_vertical_step
	_hurt_motion_ticks += 1
	if _hurt_motion_ticks > 15:
		_update_hurt_fall()


func _update_hurt_fall() -> bool:
	if not _hurt_falling:
		return false
	if _hurt_motion_ticks <= 15:
		_hurt_motion_ticks += 1
		return true
	var previous_y := position.y
	var next_y := position.y + 10.0
	var landing_y := _landing_surface_y(previous_y, next_y)
	if is_nan(landing_y):
		position.y = next_y
		if action == "击飞":
			return true
		if action != "被打" and action not in ["落", "落2"]:
			start_action("落")
		return true
	position.y = landing_y
	_hurt_falling = false
	airborne = false
	if _launched or action in ["击飞", "击落地"]:
		_launched = false
		if action != "击落地":
			start_action("击落地")
		return false
	if action != "被打":
		start_action("落地")
	return false


func configure_stage(
	ground_y: float,
	platforms: Array[Rect2],
	wall_min: float = 20.0,
	wall_max: float = 970.0
) -> void:
	_ground_y = ground_y
	_stage_platforms = platforms.duplicate()
	_wall_min = wall_min
	_wall_max = wall_max


func change_energy(amount: float) -> void:
	energy = clampf(energy + amount, 0.0, 300.0)


func _apply_source_energy_event() -> void:
	if _energy_event_applied:
		return
	for event: Dictionary in _combat.get("energy_events", []):
		if event["action"] == action and int(event["frame"]) == current_source_frame():
			change_energy(float(event["delta"]))
			_energy_event_applied = true


func _apply_summon_event() -> void:
	if _summon_applied:
		return
	for event: Dictionary in _combat.get("summon_events", []):
		if event["action"] != action or int(event["frame"]) != current_source_frame():
			continue
		change_energy(float(event.get("energy_delta", -100)))
		helper_spawn = _yfgj_spawn(event)
		_summon_applied = true
		last_event = "summon_%s" % event.get("helper_id", "helper")
		print("COMBAT_EVENT ", JSON.stringify(snapshot()))
		return


func _apply_presentation_events() -> void:
	for index in range(_combat.get("presentation_events", []).size()):
		var event: Dictionary = _combat["presentation_events"][index]
		if event["action"] != action or int(event["frame"]) != current_source_frame():
			continue
		var event_key := "%s:%d:%d" % [action, current_source_frame(), index]
		if _presentation_events_applied.has(event_key):
			continue
		_presentation_events_applied[event_key] = true
		if event.get("op") == "screen_flash":
			screen_flash_requested.emit(int(event.get("color_rgb24", 0xFFFFFF)))


func _yfgj_spawn(event: Dictionary) -> Dictionary:
	# Source yfgj(): helper._x = caster._x - 20 * (xscale <= 0 ? -1 : 1)
	# and helper faces the opponent, then gotoAndPlay(2).
	var behind := float(event.get("behind_pixels", 20.0))
	var spawn_x := position.x - behind * facing
	var helper_facing := facing
	if opponent != null and is_instance_valid(opponent):
		helper_facing = -1 if position.x >= opponent.position.x else 1
	return {
		"helper_id": str(event.get("helper_id", "")),
		"helper_swf": str(event.get("helper_swf", "")),
		"x": spawn_x,
		"y": position.y,
		"facing": helper_facing,
		"start_frame": int(event.get("start_frame", 2)),
	}


func _zhongli() -> float:
	# _root.zhongli from scripts/main.json frame_7/DoAction.as
	return 10.0


func _touch_floor() -> bool:
	# on_enterframe: _y == floorY or (_y > floorY - 10 after no ban hit)
	if not is_nan(_hit_ban_y(position)):
		return false
	return is_equal_approx(position.y, _ground_y) or position.y > _ground_y - _zhongli()


func _hit_ban_y(point: Vector2) -> float:
	# isHitBan(): _y <= ban._y && _y > ban._y - 10 && _x in [ban._x, ban._x + _width]
	for platform in _stage_platforms:
		var ban_y := platform.position.y
		if point.y <= ban_y and point.y > ban_y - _zhongli():
			if point.x >= platform.position.x and point.x <= platform.end.x:
				return ban_y
	return NAN


func _landing_surface_y(previous_y: float, next_y: float) -> float:
	var result := NAN
	if previous_y <= _ground_y and next_y >= _ground_y:
		result = _ground_y
	elif next_y > _ground_y - _zhongli() and next_y >= previous_y:
		result = _ground_y
	for platform in _stage_platforms:
		if position.x < platform.position.x or position.x > platform.end.x:
			continue
		var ban_y := platform.position.y
		var crossed := previous_y <= ban_y and next_y >= ban_y
		var in_window := next_y <= ban_y and next_y > ban_y - _zhongli()
		if (crossed or in_window) and (is_nan(result) or ban_y < result):
			result = ban_y
	return result


func _has_support_at(point: Vector2) -> bool:
	if is_equal_approx(point.y, _ground_y):
		return true
	return not is_nan(_hit_ban_y(point))


func _move_world_x(distance: float) -> void:
	position.x = clampf(position.x + distance, _wall_min, _wall_max)


func _move_forward(distance: float) -> void:
	_move_world_x(distance * facing)


func _is_special_action(label: String) -> bool:
	return label in ["必杀", "必杀1", "必杀0", "上必杀", "超必杀", "空中必杀"]


func _death_data() -> Dictionary:
	var death = _combat.get("death")
	if typeof(death) == TYPE_DICTIONARY and not death.is_empty():
		return death
	return {}


func _death_launch_label() -> String:
	var label := str(_death_data().get("launch_label", "击飞"))
	return label if not action_range(label).is_empty() else "击飞"


func _death_down_label() -> String:
	var label := str(_death_data().get("down_label", "击落地"))
	return label if not action_range(label).is_empty() else "击落地"


func _is_death_sequence_action(label: String) -> bool:
	return label == _death_launch_label() or label == _death_down_label()


func _combat_input_locked() -> bool:
	# Source gameRunning() is false when the opponent's mc.sw is true;
	# own dash/hurtSkill/standup also fail when this.sw or hp <= 0.
	if sw:
		return true
	return opponent != null and is_instance_valid(opponent) and opponent.sw


func _should_stop_dead_knockdown() -> bool:
	if not sw or action != _death_down_label():
		return false
	var stop_frame := int(_death_data().get("knockdown_stop_frame", 0))
	return stop_frame > 0 and current_source_frame() == stop_frame


func _check_dead(flying: bool) -> bool:
	# Source checkDead(fly): if sw, return; if hp <= 0 and modo != 4,
	# set sw, KOplay, and if !fly gotoAndStop("击飞").
	if sw:
		return false
	if health > 0.0:
		return false
	if _death_data().is_empty() and action_range("击飞").is_empty():
		return false
	sw = true
	last_event = "ko"
	if not flying:
		_launched = true
		_hurt_falling = true
		start_action(_death_launch_label())
	return true


func _is_hurt_action(label: String) -> bool:
	return label in ["被打", "击飞", "击落地"]


func _is_one_shot_action(label: String) -> bool:
	return label not in [
		"站立", "走", "跳", "跳2", "落", "落2", "防御", "防御2", "被打", "击飞"
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
		"sw": sw,
		"event": last_event,
		"helper_spawn": helper_spawn,
	}


func _frame_in(window: Dictionary) -> bool:
	return (
		current_source_frame() >= int(window["start_frame"])
		and current_source_frame() <= int(window["end_frame"])
	)
