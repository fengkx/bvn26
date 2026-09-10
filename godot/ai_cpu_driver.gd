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


func configure(owner_fighter: FighterRuntime, directory: String, platforms: Dictionary,
		floor_y: float, map_width: float, scope: Dictionary, external_services: Callable,
		recorded: bool = false, registry: SourceCallbackRegistry = null,
		context_override: AiBodyContext = null) -> void:
	assert(not _active and external_services.is_valid())
	fighter = owner_fighter
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
	controller.synchronize(tick)
	controller.instances.advance_children(tick)


func prepare_display_tick(tick: int) -> void:
	assert(_active and tick >= _tick)
	_tick = tick
	controller.display_tick = tick


func _observe_frame(_frame: int) -> void:
	controller.synchronize(_tick)


func advance_timeline() -> void:
	assert(_active)
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
	body.on_enterframe()
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


func _exit_tree() -> void:
	stop()


func _scope_value(key: String) -> Variant:
	assert(_scope.has(key), "Unresolved controller scope: " + key)
	return _scope[key]


func _controller_effect(name: String) -> void:
	if name.begins_with("receive:"):
		_external("receive", [name.trim_prefix("receive:")])
	elif name == "updateDirect":
		body.updateDirect()
	else:
		_external(name, [])


func _body_call(name: String, args: Array) -> void:
	assert(body.has_method(name))
	body.callv(name, args)


func _external(name: String, args: Array) -> Variant:
	assert(services.is_valid(), "Unconnected CPU service: " + name)
	return services.call(name, args)


func _frame_service(event: Dictionary) -> void:
	match event["op"]:
		"root_position", "frame_child_effect":
			_external(event["op"], [event])
			return
		"inline_frame":
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
				var value: Variant = fighter.ai_predicate_context.read_field(condition["field"])
				match condition["operator"]:
					"gt":
						if value == null or not value > condition["value"]: return
					"eq":
						if value != condition["value"]: return
					_: assert(false, "Uncompiled frame condition")
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
