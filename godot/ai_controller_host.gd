class_name AiControllerHost
extends RefCounted

var fighter: FighterRuntime
var context: AiPredicateContext
var instances := AiControllerInstances.new()
var display_tick: int = 0
var effects: Callable
var body_calls: Callable
var scope_lookup: Callable
var key_reader: Callable
var _controller_script: Script
var _hooks: Array


class Receiver extends RefCounted:
	var host_ref: WeakRef
	var source_method: String
	var counter_label: String

	func receive() -> void:
		var host: AiControllerHost = host_ref.get_ref()
		assert(host.effects.is_valid())
		host.effects.call("counter:" + counter_label if source_method == "checkHit" else "receive:" + source_method)
		host.synchronize(host.display_tick)


class Projectile extends RefCounted:
	var host_ref: WeakRef
	var model: Dictionary
	var last_advance_tick: int = -1
	var source_path: String
	var generation: int
	var instance_name: String
	var pending_natural_frames: Array[int] = []

	func current_source_name() -> Variant:
		var host: AiControllerHost = host_ref.get_ref()
		return instance_name if host != null and host.instances.alive(source_path, generation) else null

	func rename_from_root(source_name: String, target_name: String) -> void:
		if instance_name == source_name:
			instance_name = target_name

	func queue_frame_script(frame: int) -> void:
		var events: Array = model.get("rename_frames", []).duplicate()
		events.append_array(model.get("frame_events", []))
		events.append_array(model.get("timeline_events", []))
		for event: Dictionary in events:
			if int(event["frame"]) == frame:
				var host: AiControllerHost = host_ref.get_ref()
				assert(not host.fighter.source_child_frame_requested.get_connections().is_empty(), "Unconnected projectile frame queue")
				host.fighter.source_child_frame_requested.emit(run_frame_script.bind(frame))
				return

	func run_frame_script(frame: int) -> void:
		if current_source_name() == null:
			return
		for rename: Dictionary in model.get("rename_frames", []):
			if int(rename["frame"]) == frame:
				instance_name = rename["instance_name"]
				if rename.has("name_field"):
					var host: AiControllerHost = host_ref.get_ref()
					var variables := host.fighter.instance_source_variables(model["instance_name"])
					assert(variables.has(rename["name_field"]), "Undeclared projectile rename local")
					instance_name = str(variables[rename["name_field"]])
				if rename.get("random_suffix", false):
					var host: AiControllerHost = host_ref.get_ref()
					instance_name += str(host.fighter.source_random.next_value(str(rename["random_site"])))
		for event: Dictionary in model.get("frame_events", []):
			if int(event["frame"]) == frame:
				var host: AiControllerHost = host_ref.get_ref()
				match event["op"]:
					"screen_flash":
						host.fighter.screen_flash_requested.emit(int(event["color_rgb24"]))
					"opponent_action_goto":
						if host.context.read_field("opponent_action") == event["action"]:
							host.goto_label(event["label"], true)
							if current_source_name() != null and event.get("stop_child", false):
								host.fighter.set_instance_clip_frame(model["instance_name"], frame, false)
		for event: Dictionary in model.get("timeline_events", []):
			if int(event["frame"]) != frame:
				continue
			var host: AiControllerHost = host_ref.get_ref()
			assert(not host.fighter.source_child_frame_requested.get_connections().is_empty(),
				"Unconnected nested timeline event queue")
			host.fighter.source_child_frame_requested.emit(
				_play_nested_timeline_sound.bind(frame, event["event"])
			)

	func _play_nested_timeline_sound(frame: int, event: Dictionary) -> void:
		var host: AiControllerHost = host_ref.get_ref()
		if current_source_name() == null or host == null:
			return
		var instance_id := "root/%d:%d:%d#%d" % [
			int(model.get("source_depth", -1)),
			int(model.get("source_sprite_id", -1)),
			int(model.get("source_placement_frame", -1)),
			generation,
		]
		host.fighter.play_source_timeline_sound(
			event,
			instance_id,
			int(model.get("source_sprite_id", -1)),
			frame,
			str(current_source_name())
		)

	func advance_timeline(tick: int) -> void:
		if last_advance_tick == tick:
			return
		last_advance_tick = tick
		var host: AiControllerHost = host_ref.get_ref()
		var before := host.fighter.instance_clip_frame(model["instance_name"])
		host.fighter._advance_clip_playhead(model["instance_name"], model)
		var after := host.fighter.instance_clip_frame(model["instance_name"])
		if after != before:
			pending_natural_frames.append(after)
		host.fighter.refresh_display()

	func enter_frame() -> void:
		var host: AiControllerHost = host_ref.get_ref()
		if not model.get("frame_only", false) and not host.fighter.root_zhanting:
			if host.fighter.run_projectile_callback(model) and model.has("on_hit_goto_frame"):
				queue_frame_script(int(model["on_hit_goto_frame"]))
			host.fighter.refresh_display()
		# Natural child frames execute at the child's registration, before older
		# receivers query its name. Callback-generated gotos remain deferred.
		for frame: int in pending_natural_frames:
			run_frame_script(frame)
		pending_natural_frames.clear()


class SourceChild extends RefCounted:
	var host_ref: WeakRef
	var model: Dictionary

	func enter_frame() -> void:
		var host: AiControllerHost = host_ref.get_ref()
		var fighter := host.fighter
		if fighter.root_zhanting or fighter.opponent == null:
			return
		var frame := fighter.current_source_frame()
		for placement: Dictionary in fighter._frames[frame]["display_list"]:
			if int(placement["depth"]) != int(model["depth"]) or int(placement["placed_frame"]) != int(model["placement_frame"]) or int(placement["character_id"]) != int(model["controller_id"]):
				continue
			match model["source_child_operation"]:
				"self_contact_goto":
					var own := fighter.source_placement_global_bounds(placement, frame)
					var target := fighter.opponent.instance_global_bounds("bdmn")
					if own.has_area() and target.has_area() and SourceHitTest.intersects(own, target):
						host.goto_label(model["target_label"], true)
				"opponent_follow":
					if not fighter.opponent.sw:
						var matrix: Dictionary = placement["matrix"]
						fighter.opponent.source_x = fighter.source_x + float(matrix.get("translateX", 0)) / 20.0 * fighter.scale.x
						fighter.opponent.source_y = fighter.source_y + float(matrix.get("translateY", 0)) / 20.0
			return


class Adapter extends RefCounted:
	var host_ref: WeakRef
	var path: String
	var generation: int

	func source_key(key: String) -> Variant:
		var host: AiControllerHost = host_ref.get_ref()
		assert(host.key_reader.is_valid(), "Player controller requires source input")
		return host.key_reader.call(key)

	func read_field(key: String) -> Variant:
		return host_ref.get_ref().context.read_field(key)

	func write_field(key: String, value: Variant) -> void:
		host_ref.get_ref().context.write_field(key, value)

	func resolve_controller_scope(key: String) -> Variant:
		var host: AiControllerHost = host_ref.get_ref()
		assert(host.scope_lookup.is_valid(), "Controller scope must be supplied by the source host")
		return host.scope_lookup.call(key)

	func sensor_hit(key: String) -> Variant:
		return host_ref.get_ref().context.sensor_hit(key)

	func body_hit(key: String, target: String = "bdmn") -> Variant:
		return host_ref.get_ref().context.body_hit(key, target)

	func power_field(key: String) -> Variant:
		return host_ref.get_ref().context.power_field(key)

	func goto_label(label: String, play: bool) -> void:
		host_ref.get_ref().goto_label(label, play)

	func controller_alive() -> bool:
		var host: AiControllerHost = host_ref.get_ref()
		return host != null and host.instances.alive(path, generation)

	func effect(name: String) -> void:
		var host: AiControllerHost = host_ref.get_ref()
		assert(host.effects.is_valid(), "Unconnected source effect: " + name)
		host.effects.call(name)

	func move_axis(axis: String, value: Variant) -> void:
		var host: AiControllerHost = host_ref.get_ref()
		if axis == "moveX":
			# Wrapper moveX only adds; BODY and GameWorld own wall clamping.
			host.fighter.source_x += float(value) * host.fighter.facing
		elif axis == "moveY":
			host.fighter.source_y += float(value)
		else:
			assert(false, "Unknown source movement: " + axis)

	func body_call(name: String, args: Array) -> void:
		var host: AiControllerHost = host_ref.get_ref()
		assert(host.body_calls.is_valid(), "Unconnected source BODY function: " + name)
		host.body_calls.call(name, args)


func configure(owner_fighter: FighterRuntime, directory: String) -> void:
	fighter = owner_fighter
	fighter.ai_timeline_controlled = true
	context = fighter.ai_predicate_context
	_controller_script = load(directory.path_join("controller.gd"))
	var metadata: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(directory.path_join("controller.json")))
	assert(metadata["source_swf"]["sha256"] == fighter.ai_source_state.spec["source_swf"]["sha256"])
	_hooks = metadata["hooks"].duplicate()
	_hooks.append_array(metadata["receiver_hooks"])
	_hooks.append_array(metadata["projectile_hooks"])
	for hook: Dictionary in _hooks:
		# JSON numbers are floats in Godot; Array.has uses Variant type identity.
		# Source frame identity is integer-valued on both sides of membership.
		hook["member_frames"] = PackedInt32Array(hook["member_frames"])
	# Source placements are visited in timeline/depth order. A shared registry
	# then dispatches newest registrations first, independent of current depth.
	_hooks.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return int(a["depth"]) < int(b["depth"]))
	instances.clear()


func synchronize(tick: int) -> void:
	display_tick = tick
	instances.synchronize(_hooks, fighter.current_source_frame(), tick, _create_instance)


func dispatch(ordered_paths: Array, tick: int) -> void:
	display_tick = tick
	instances.dispatch(ordered_paths, tick)


func paths_by_descending_depth() -> Array:
	var ordered := _hooks.duplicate()
	ordered.sort_custom(func(left: Dictionary, right: Dictionary) -> bool:
		return int(left["depth"]) > int(right["depth"]))
	return ordered.map(func(hook: Dictionary) -> String: return hook["path"])


func goto_frame(frame: int, play: bool) -> void:
	fighter.source_goto_frame(frame, play)
	synchronize(display_tick)


func goto_label(label: String, play: bool) -> void:
	# Shared controls can reference labels absent from a particular source form.
	# Native Flash leaves the playhead unchanged for those authored requests.
	if fighter.action_range(label).is_empty():
		return
	fighter.goto_ai_label(label, play)
	# Display-list changes precede the generated caller's survival check.
	# FighterRuntime queues target state writes for its frame-action phase.
	synchronize(display_tick)


func _create_instance(hook: Dictionary, generation: int) -> RefCounted:
	if hook.has("source_child_operation"):
		var child := SourceChild.new()
		child.host_ref = weakref(self)
		child.model = hook
		return child
	if hook.has("projectile"):
		var projectile := Projectile.new()
		projectile.host_ref = weakref(self)
		projectile.model = hook["projectile"].duplicate(true)
		projectile.source_path = hook["path"]
		projectile.generation = generation
		projectile.instance_name = projectile.model["instance_name"]
		fighter.source_projectiles[projectile.instance_name] = weakref(projectile)
		if projectile.model.has("initial_speed_field"):
			projectile.model["initial_speed"] = float(context.read_field(projectile.model["initial_speed_field"])) * float(projectile.model["initial_speed_factor"])
		fighter.set_instance_local_offset(projectile.model["instance_name"], Vector2.ZERO)
		fighter._start_clip_playhead(projectile.model["instance_name"], projectile.model)
		if not projectile.model.get("timeline_events", []).is_empty():
			fighter.mark_source_timeline_event_driver(projectile.model["instance_name"])
		projectile.queue_frame_script(1)
		return projectile
	if hook.has("receiver"):
		var receiver := Receiver.new()
		receiver.host_ref = weakref(self)
		receiver.source_method = hook["receiver"]
		receiver.counter_label = str(hook.get("counter_label", ""))
		return receiver
	var adapter := Adapter.new()
	adapter.host_ref = weakref(self)
	adapter.path = hook["path"]
	adapter.generation = generation
	var controller = _controller_script.new({})
	controller.bind_adapter(adapter)
	return controller
