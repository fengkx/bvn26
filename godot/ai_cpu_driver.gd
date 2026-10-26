class_name AiCpuDriver
extends Node

var controller := AiControllerHost.new()
var body_context: AiBodyContext
var body: RefCounted
var timeouts: AiSourceTimeouts
var fighter: FighterRuntime
var services: Callable
var _scope: Dictionary
var _tick: int = 0
var _active: bool = false
var _random_started: bool = false
var _ordered_paths: Array = []
var callback_registry: SourceCallbackRegistry
var _body_registration: int = 0
var initial_frame_count: int = -1
var source_form_profiles: Dictionary = {}
var source_form_context: SourceFormContext
var _pending_form: Dictionary = {}
var _pending_form_tick: int = -1
var _controller_directory: String
var _form_current_callback: Callable
var _form_callback_owner: RefCounted
signal body_replaced



func configure(owner_fighter: FighterRuntime, directory: String, platforms: Dictionary,
		floor_y: float, map_width: float, scope: Dictionary, external_services: Callable,
		recorded: bool = false, registry: SourceCallbackRegistry = null,
		context_override: AiBodyContext = null) -> void:
	assert(not _active and external_services.is_valid())
	fighter = owner_fighter
	_controller_directory = directory
	_tick = 0
	services = external_services
	_scope = scope.duplicate()
	controller.configure(fighter, directory)
	callback_registry = registry
	controller.instances.registry = registry
	fighter.source_frame_changed.connect(_observe_frame)
	fighter.ai_frame_service_requested.connect(_frame_service)
	_ordered_paths = controller.paths_by_descending_depth()
	controller.scope_lookup = _scope_value
	controller.effects = _controller_effect
	controller.body_calls = _body_call
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("body.json")))
	body_context = context_override if context_override != null else AiBodyContext.new(fighter)
	body_context.configure(controller, metadata, platforms)
	body_context.floor_y = floor_y
	body_context.map_size_x = map_width
	body_context.external_call = _external
	body = load(directory.path_join("body.gd")).new({})
	body.adapter = body_context
	fighter.source_body = body
	if callback_registry != null:
		_body_registration = callback_registry.register(self, "run_body", _tick)
	timeouts = AiSourceTimeouts.new()
	timeouts.recorded = recorded
	add_child(timeouts)
	body_context.timeout_scheduler = timeouts
	body_context.body_target = weakref(body)
	_active = true


func start_random(random: SourceRandom, difficulty: int, recorded: bool = false) -> void:
	assert(_active and not _random_started)
	fighter.ai_random_clock.initialize(fighter.ai_source_state, random, difficulty, recorded)
	_random_started = true


func begin_display_tick(tick: int) -> void:
	assert(_active and tick >= _tick)
	_tick = tick
	if not fighter.source_body_available:
		return
	controller.synchronize(tick)
	controller.instances.advance_children(tick)


func prepare_display_tick(tick: int) -> void:
	assert(_active and tick >= _tick)
	_tick = tick
	controller.display_tick = tick


func _observe_frame(_frame: int) -> void:
	if fighter.source_body_available and _pending_form.is_empty():
		controller.synchronize(_tick)


func advance_timeline() -> void:
	assert(_active)
	if not _pending_form.is_empty():
		if _tick <= _pending_form_tick:
			return
		_install_pending_form()
		return
	fighter.advance_retained_visual_clips()
	if fighter.timeline_playing:
		fighter.advance_ai_timeline()
	else:
		fighter.refresh_display()


func run_controllers(ordered_paths: Array) -> void:
	assert(_active)
	controller.dispatch(ordered_paths, _tick)


func run_body() -> void:
	assert(_active)
	if not fighter.source_body_available:
		return
	var epoch := fighter.source_body_epoch
	body.on_enterframe()
	if epoch != fighter.source_body_epoch:
		return
	controller.synchronize(_tick)
	if initial_frame_count >= 0:
		run_target_frames(false, initial_frame_count)
		initial_frame_count = -1


func run_enter_frame(profile: Dictionary) -> void:
	# This orders the compiled BODY subtree only, not both fighters or timers.
	var rules: Dictionary = profile["measured_rules"]["advancing_timeline"]
	assert(rules["child_clip_enter_frame_runs_before_root_on_enter_frame"] == true)
	assert(rules["sibling_clip_enter_frame_order"] == "descending_display_depth")
	run_controllers(_ordered_paths)
	run_body()


func run_target_frames(drain_nested: bool = true, initial_limit: int = -1) -> void:
	assert(_active)
	fighter.run_frame_actions(drain_nested, initial_limit)
	if fighter.source_body_available:
		controller.synchronize(_tick)


func stop() -> void:
	if not _active:
		return
	_active = false
	if fighter.source_body == body:
		fighter.source_body = null
	fighter.source_projectiles.clear()
	fighter.ai_timeline_controlled = false
	fighter.independent_visual_clock = false
	fighter._retained_visual_clips.clear()
	fighter.ai_frame_service_requested.disconnect(_frame_service)
	fighter.source_frame_changed.disconnect(_observe_frame)
	if _random_started:
		fighter.ai_random_clock.cancel()
		_random_started = false
	timeouts.clear()
	timeouts.queue_free()
	controller.instances.clear()
	controller.instances.registry = null
	if callback_registry != null:
		callback_registry.unregister(_body_registration)
	callback_registry = null
	# Bound callables must not keep this completed match attached to its actors.
	controller.effects = Callable()
	controller.body_calls = Callable()
	controller.scope_lookup = Callable()
	controller.key_reader = Callable()
	controller.context.use_ai = true
	controller.context = null
	controller.fighter = null
	body_context.external_call = Callable()
	body_context.timeout_scheduler = null
	body = null
	body_context = null
	fighter = null
	services = Callable()
	_scope.clear()
	_ordered_paths.clear()
	source_form_profiles = {}
	source_form_context = null
	_pending_form = {}
	_form_current_callback = Callable()
	_form_callback_owner = null


func _exit_tree() -> void:
	stop()


func _scope_value(key: String) -> Variant:
	assert(_scope.has(key), "Unresolved controller scope: " + key)
	return _scope[key]


func _controller_effect(name: String) -> void:
	if name.begins_with("receive:"):
		_external("receive", [name.trim_prefix("receive:")])
	elif name.begins_with("counter:"):
		_external("counter", [name.trim_prefix("counter:")])
	elif name == "updateDirect":
		body.updateDirect()
	elif name == "bdfyxg":
		fighter.emit_source_guard_effect(1)
	elif name == "bdfyxg2":
		fighter.emit_source_guard_effect(2)
	else:
		_external(name, [])


func _body_call(name: String, args: Array) -> void:
	assert(body.has_method(name))
	body.callv(name, args)


func _external(name: String, args: Array) -> Variant:
	assert(services.is_valid(), "Unconnected CPU service: " + name)
	return services.call(name, args)


func _movement_operand(expression: Dictionary) -> float:
	match expression["op"]:
		"constant":
			return float(expression["value"])
		"read":
			var value: Variant = fighter.ai_source_state.read_field(expression["field_name"])
			return NAN if value == null else float(value)
		"negate":
			return -_movement_operand(expression["operand"])
		"positive":
			return _movement_operand(expression["operand"])
		"add":
			return _movement_operand(expression["left"]) + _movement_operand(expression["right"])
		"subtract":
			return _movement_operand(expression["left"]) - _movement_operand(expression["right"])
		"multiply":
			return _movement_operand(expression["left"]) * _movement_operand(expression["right"])
		"divide":
			return _movement_operand(expression["left"]) / _movement_operand(expression["right"])
	assert(false, "Unknown compiled movement operand: " + str(expression))
	return NAN


func _frame_service(event: Dictionary) -> void:
	match event["op"]:
		"body_form_call":
			assert(source_form_context != null and str(event.method) == "wankai")
			body.wankai()
			return
		"parent_form_goto":
			assert(not event.get("play", false), "Parent gotoAndPlay requires a parent timeline clock")
			request_parent_frame(int(event.target_frame))
			return
		"form_prepare_slot":
			_prepare_form_slot(event)
			return
		"form_start_interval":
			assert(source_form_context != null and _form_current_callback.is_valid())
			var slot := "feiint" if fighter.ai_source_state.read_field(str(event.selector_field)) == 1 else "feiint2"
			source_form_context.root_intervals.assign_interval(slot, _form_current_callback, int(event.delay_ms))
			return
		"update_direct":
			body.updateDirect()
			return
		"wrapper_move":
			var pixels := _movement_operand(event["pixels_expression"]) if event.has("pixels_expression") else float(event["pixels"])
			# Wrapper moveY adds Y, unlike the child controller's upward moveY.
			if event["axis"] == "moveX":
				fighter.source_x += pixels * fighter.facing
			else:
				assert(event["axis"] == "moveY")
				fighter.source_y += pixels
			return
		"root_position", "frame_child_effect":
			_external(event["op"], [event])
			return
		"inline_frame":
			var epoch := fighter.source_body_epoch
			for call in event["calls"]:
				_frame_service(call)
				if epoch != fighter.source_body_epoch:
					return
			return
		"frame_hit_test":
			fighter.ai_source_state.values[event["field_name"]] = fighter.ai_predicate_context.body_hit(event["instance"])
			return
		"follow_clip":
			var target := str(event["instance"])
			for authored: String in fighter.source_projectiles:
				var clip: RefCounted = fighter.source_projectiles[authored].get_ref()
				if clip != null and clip.current_source_name() == target:
					target = authored
					break
			if fighter.opponent == null:
				return
			var origin := fighter.named_instance_origin(target)
			if origin == Vector2.INF:
				return
			var offset := fighter.instance_local_offset(target)
			var direction := 1.0 if fighter.scale.x > 0 else -1.0
			var relative_x: float = (fighter.opponent.source_x - fighter.source_x) * direction
			if bool(event["place_x"]) and (not bool(event["front_only"]) or relative_x > 0):
				offset.x = relative_x - origin.x
			if bool(event["place_y"]):
				offset.y = fighter.opponent.source_y - fighter.source_y - origin.y
			fighter.set_instance_local_offset(target, offset)
			fighter._placement_owned[target] = true
			fighter.refresh_display()
			return
		"child_timeline_goto":
			var authored: String = event["authored_name"]
			if fighter.source_projectiles.has(authored):
				var clip: RefCounted = fighter.source_projectiles[authored].get_ref()
				if clip != null and clip.current_source_name() == event["instance"]:
					fighter.set_instance_clip_frame(authored, int(event["target_frame"]), bool(event["play"]))
					clip.queue_frame_script(int(event["target_frame"]))
					fighter.refresh_display()
			return
		"opponent_visibility":
			fighter.ai_predicate_context.write_field("opponent_visible", event["value"])
			return
		"parent_frame_field":
			fighter.write_parent_field(event["field_name"], event["value"])
			return
		"parent_conditional_frame":
			if fighter.read_parent_field(event["field_name"]) == event["value"]:
				for call in event["calls"]:
					_frame_service(call)
			return
		"frame_field":
			var key: String = event["field_name"]
			var value: Variant = event["value"]
			if event["operator"] == "-=":
				var current: Variant = fighter.energy if key == "ql" else fighter.ai_source_state.read_field(key)
				value = current - value
			else:
				assert(event["operator"] == "=")
			if key == "ql":
				fighter.energy = float(value)
			else:
				fighter.ai_source_state.values[key] = value
				if key in ["hited", "beida", "bs", "sw"]:
					fighter.set(key, value)
			return
		"conditional_frame":
			for condition in event["conditions"]:
				if not _frame_condition(condition):
					for call in event.get("else_calls", []):
						_frame_service(call)
					return
			if event.has("alternatives"):
				var matched := false
				for condition in event["alternatives"]:
					if _frame_condition(condition):
						matched = true
						break
				if not matched: return
			for call in event["calls"]:
				_frame_service(call)
			return
		"color_reset":
			fighter.reset_ai_colors()
			return
		"color_write":
			match event["field_name"]:
				"_csn": fighter.ai_color_state.index = int(event["value"])
				"_cgap": fighter.ai_color_state.gap = int(event["value"])
				_: assert(false, "Uncompiled color field")
			return
		"timeline_goto_frame":
			controller.goto_frame(int(event["target_frame"]), bool(event["play"]))
			return
		"timeline_goto":
			controller.goto_label(event["label"], event["play"])
			return
		"timeline_play":
			fighter.timeline_playing = true
			return
		"timeline_stop":
			fighter.timeline_playing = false
			return
	_external("frame_super", [event])
	fighter.last_super = event.duplicate()
	fighter.super_event_applied.emit(fighter.last_super)


func _frame_condition(condition: Dictionary) -> bool:
	var context := fighter.ai_predicate_context
	var value: Variant = context.body_hit(condition["instance"]) if condition.has("instance") else context.read_field(condition["field"])
	match condition["operator"]:
		"gt": return value != null and value > condition["value"]
		"eq": return value == condition["value"]
		_: assert(false, "Uncompiled frame condition")
	return false


func configure_forms(profiles: Dictionary, intervals: SourceRootIntervals,
		root_values: Dictionary, parent_frame: int = 1) -> void:
	assert(_active and source_form_context == null and fighter.player_slot in ["p1", "p2"])
	var prepared := {}
	for frame in profiles:
		var entry: Dictionary = profiles[frame]
		var profile := SourceFormProfile.prepare(entry.directory, str(fighter.ai_source_state.spec.source_swf.sha256))
		assert(not profile.has("error"), str(profile.get("error", "")))
		assert(entry.get("load_declarations") is Array)
		prepared[str(frame)] = {"profile": profile, "load_declarations": entry.load_declarations}
	# These source packages are immutable rollback configuration; pending
	# replacement selects an entry, never edits it. Teardown drops references.
	for entry: Dictionary in prepared.values():
		entry.make_read_only()
	prepared.make_read_only()
	source_form_profiles = prepared
	assert(fighter.ai_source_state.spec.get("form_initialization", {}).get("bind_opponent_slot") == true, "Missing source initial wrapper slot binding")
	fighter.ai_source_state.values["pn"] = 2 if fighter.player_slot == "p1" else 1
	fighter.source_parent_frame = parent_frame
	source_form_context = SourceFormContext.new(fighter, intervals, root_values, fighter.player_slot, _form_effect)
	body_context.form_context = source_form_context
	assert(body.has_method("wankai") and body.has_method("doWanKai"), "Base BODY lacks compiled form functions")
	_form_callback_owner = null
	_form_current_callback = Callable(body, "feixue")


func request_parent_frame(frame: int) -> bool:
	assert(source_form_context != null, "Parent replacement has no root owner")
	if frame == fighter.source_parent_frame:
		return true
	assert(source_form_profiles.has(str(frame)), "Uncompiled parent frame %d for %s" % [frame, fighter.fighter_directory])
	assert(_pending_form.is_empty(), "Cannot replace an uninitialized replacement body")
	_pending_form = source_form_profiles[str(frame)]
	_pending_form_tick = _tick
	fighter.source_parent_frame = frame
	controller.instances.clear()
	if callback_registry != null:
		callback_registry.unregister(_body_registration)
		_body_registration = 0
	initial_frame_count = -1
	fighter.retire_source_body()
	body = null
	# Root intervals and captured body timeouts deliberately survive this step.
	return false


func _install_pending_form() -> void:
	var pending := _pending_form
	var old_key_reader := controller.key_reader
	var old_use_ai: Variant = body_context.use_ai
	var platforms := body_context.source_platforms
	fighter.independent_visual_clock = true
	fighter.install_source_profile(pending.profile, pending.load_declarations)
	_controller_directory = pending.profile.controller_directory
	controller.configure(fighter, _controller_directory)
	controller.context.use_ai = old_use_ai
	controller.key_reader = old_key_reader
	body_context.configure(controller, pending.profile.body_metadata, platforms)
	body = pending.profile.body_script.new({})
	body.adapter = body_context
	body_context.body_target = weakref(body)
	fighter.source_body = body
	_form_callback_owner = null
	_form_current_callback = Callable(body, "feixue")
	_ordered_paths = controller.paths_by_descending_depth()
	_pending_form = {}
	_pending_form_tick = -1
	if callback_registry != null:
		_body_registration = callback_registry.register(self, "run_body", _tick)
	body.doWanKai()
	if not fighter.read_parent_field("万解"):
		body.updateDirect()
	# doWanKai places the target subtree before this display advance. Its
	# child timelines advance with the new body (native Yihu stage trace).
	fighter.advance_retained_visual_clips()
	# The new instance enters its second source frame before the next observer,
	# but its enterFrame registration cannot run in this placement tick.
	fighter.advance_ai_timeline()
	controller.synchronize(_tick)
	body_replaced.emit()


func _form_effect(operation: String, arguments: Array) -> Variant:
	match operation:
		"_parent.nextFrame()":
			return request_parent_frame(fighter.source_parent_frame + 1)
		"trace":
			print(str(arguments[0]))
		"root_y":
			_external("root_position", [{"axis": "y", "operator": "=", "pixels": arguments[0]}])
		"_parent.updateGJL()":
			_refresh_form_power(fighter)
		"_root.game[\"p\" + pn].updateGJL()":
			assert(fighter.opponent != null)
			_refresh_form_power(fighter.opponent)
		"AImain.gotoAndStop(1)":
			fighter.ai_senses.sensors = {}
		"AImain.unloadMovie()":
			fighter.ai_senses.sensors = {}
		"AImain.gotoAndStop(2)":
			fighter.ai_senses = AiSenses.new()
			fighter.ai_senses.configure(fighter, fighter.ai_source_state.spec)
		_:
			assert(false, "Uncompiled form effect: " + operation)
	return null


func _refresh_form_power(target: FighterRuntime) -> void:
	target.source_power_fields = target.ai_source_state.spec.base_power_fields
	if target.opponent != null:
		target.ai_source_state.values["pw"] = target.opponent.ai_source_state.spec.base_power_fields
	assert(target.opponent != null)
	var helper_key := "helper_power:" + target.opponent.player_slot
	assert(source_form_context.root_values.has(helper_key), "Missing root helper power binding: " + helper_key)
	target.ai_source_state.values["fzpw"] = source_form_context.root_values[helper_key]


func _prepare_form_slot(event: Dictionary) -> void:
	assert(source_form_context != null and event.callback == "slot_health")
	if fighter.ai_source_state.read_field("pn") != event.pn:
		return
	fighter.ai_source_state.values["zn"] = event.zn
	source_form_context.root_values[str(event.slot) + "bs"] = event.selection
	source_form_context.transfer["ql"] = fighter.energy
	source_form_context.transfer["hp"] = fighter.health
	var target := fighter if fighter.player_slot == event.slot else fighter.opponent
	assert(target != null and target.player_slot == event.slot)
	var closure := preload("res://source_slot_health_callback.gd").new()
	closure.target = weakref(target)
	assert(source_form_context.root_values.has("maxhp"), "Missing root maxhp binding")
	closure.root_values = source_form_context.root_values
	_form_callback_owner = closure
	_form_current_callback = Callable(closure, "deliver")
