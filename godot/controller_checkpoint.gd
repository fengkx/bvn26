extends RefCounted

# Reconstruction is deliberately separate from source placement. Calling
# _create_instance while restoring would reset child clocks and queue frame 1.
const Values := preload("res://simulation_state.gd")


static func identity(path: String, generation: int) -> String:
	return "%s#%d" % [path, generation]


static func save(host: AiControllerHost, retained_targets: Array = []) -> Dictionary:
	var entries := []
	var targets := {}
	var retired := []
	for path: String in host.instances._instances:
		var instance: Dictionary = host.instances._instances[path]
		var target: RefCounted = instance.controller
		var state := {}
		var kind := "controller"
		if target is AiControllerHost.Projectile:
			kind = "projectile"
			state = _projectile_state(target)
		elif target is AiControllerHost.Receiver:
			kind = "receiver"
			state = {"source_method": target.source_method}
		else:
			for field in _controller_fields(target):
				state[field] = target.get(field)
		var problem := Values.validate_value(state)
		if not problem.is_empty():
			return {"error": path + ": " + problem}
		var key := identity(path, int(instance.generation))
		targets[target] = key
		entries.append({"path": path, "generation": instance.generation,
			"placed_tick": instance.placed_tick, "method": instance.method,
			"registration": instance.get("registration", 0), "kind": kind,
			"state": state.duplicate(true)})
	# Preserve tombstones too: FighterRuntime tests alias presence as well as
	# liveness. Removing a dead alias changes the source lookup path.
	var aliases := {}
	var retained := retained_targets.duplicate()
	for reference: WeakRef in host.fighter.source_projectiles.values():
		var target: Object = reference.get_ref()
		if target != null:
			retained.append(target)
	for target in retained:
		if targets.has(target):
			continue
		if not target is AiControllerHost.Projectile or target.host_ref.get_ref() != host:
			return {"error": "Retained target is not a projectile owned by this host"}
		var state := _projectile_state(target)
		var problem := Values.validate_value(state)
		if not problem.is_empty():
			return {"error": problem}
		targets[target] = identity(target.source_path, target.generation)
		retired.append({"path": target.source_path, "generation": target.generation,
			"placed_tick": 0, "method": "enter_frame", "registration": 0,
			"kind": "projectile", "state": state})
	for name: String in host.fighter.source_projectiles:
		var target: Object = host.fighter.source_projectiles[name].get_ref()
		aliases[name] = targets.get(target)
	return {"version": 1, "script": host._controller_script.resource_path,
		"display_tick": host.display_tick, "next_generation": host.instances._next_generation,
		"entries": entries, "retired": retired, "aliases": aliases}


static func prepare(host: AiControllerHost, snapshot: Variant) -> Dictionary:
	var problem := Values.validate_value(snapshot)
	if not problem.is_empty():
		return {"error": problem}
	if not snapshot is Dictionary or snapshot.get("version") != 1 or snapshot.get("script") != host._controller_script.resource_path:
		return {"error": "Incompatible controller checkpoint"}
	for key in ["display_tick", "next_generation"]:
		if not snapshot.get(key) is int or snapshot[key] < 0:
			return {"error": "Invalid controller counter: " + key}
	if not snapshot.get("entries") is Array or not snapshot.get("retired") is Array or not snapshot.get("aliases") is Dictionary:
		return {"error": "Missing controller instances/aliases"}
	var hooks := {}
	for hook: Dictionary in host._hooks:
		hooks[hook.path] = hook
	var restored := {}
	var targets := {}
	var generations := {}
	var registrations := {}
	var all_entries: Array = snapshot.entries + snapshot.retired
	for index in all_entries.size():
		var entry: Variant = all_entries[index]
		var active: bool = index < snapshot.entries.size()
		if not entry is Dictionary or not entry.get("path") is String or not hooks.has(entry.path):
			return {"error": "Unknown source controller path"}
		if (active and restored.has(entry.path)) or not entry.get("state") is Dictionary:
			return {"error": "Repeated controller path or missing state"}
		for key in ["generation", "placed_tick", "registration"]:
			if not entry.get(key) is int or entry[key] < 0:
				return {"error": "Invalid controller instance counter"}
		if entry.generation < 1 or entry.generation > snapshot.next_generation or generations.has(entry.generation):
			return {"error": "Invalid controller generation"}
		generations[entry.generation] = true
		if entry.registration > 0:
			if registrations.has(entry.registration):
				return {"error": "Repeated callback registration"}
			registrations[entry.registration] = true
		var hook: Dictionary = hooks[entry.path]
		if not active and (not hook.has("projectile") or entry.registration != 0):
			return {"error": "Invalid retired projectile"}
		if entry.get("method") != hook.method:
			return {"error": "Controller method does not match source hook"}
		var target: RefCounted
		var state: Dictionary = entry.state
		if hook.has("projectile"):
			if entry.get("kind") != "projectile" or not state.get("model") is Dictionary or not state.get("instance_name") is String:
				return {"error": "Invalid projectile state"}
			if not state.get("last_advance_tick") is int or not state.get("pending_natural_frames") is Array:
				return {"error": "Invalid projectile clock"}
			var model: Dictionary = hook.projectile.duplicate(true)
			if model.has("initial_speed_field"):
				if not (state.model.get("initial_speed") is int or state.model.get("initial_speed") is float):
					return {"error": "Missing captured projectile speed"}
				model.initial_speed = state.model.initial_speed
			if state.model != model:
				return {"error": "Projectile model differs from loaded source data"}
			for frame in state.pending_natural_frames:
				if not frame is int or frame < 1:
					return {"error": "Invalid pending child frame"}
			target = AiControllerHost.Projectile.new()
			target.host_ref = weakref(host)
			target.source_path = entry.path
			target.generation = entry.generation
			target.model = state.model.duplicate(true)
			target.instance_name = state.instance_name
			target.last_advance_tick = state.last_advance_tick
			target.pending_natural_frames.assign(state.pending_natural_frames)
		elif hook.has("receiver"):
			if entry.get("kind") != "receiver" or state.get("source_method") != hook.receiver:
				return {"error": "Invalid receiver state"}
			target = AiControllerHost.Receiver.new()
			target.host_ref = weakref(host)
			target.source_method = state.source_method
			target.counter_label = str(hook.get("counter_label", ""))
		else:
			if entry.get("kind") != "controller":
				return {"error": "Invalid controller type"}
			target = host._controller_script.new({})
			var fields := _controller_fields(target)
			if fields.size() != state.size():
				return {"error": "Incomplete generated controller locals"}
			for field in fields:
				if not state.has(field):
					return {"error": "Missing controller local: " + field}
				var value: Variant = state[field]
				for property in target.get_property_list():
					if property.name == field and int(property.type) != TYPE_NIL and typeof(value) != int(property.type):
						return {"error": "Invalid controller local type: " + field}
				target.set(field, value.duplicate(true) if value is Array or value is Dictionary else value)
			var adapter := AiControllerHost.Adapter.new()
			adapter.host_ref = weakref(host)
			adapter.path = entry.path
			adapter.generation = entry.generation
			# bind_adapter reads source scope and overwrites touchFloor; restoration
			# must bind the service without re-running initialization.
			target.adapter = adapter
		var instance := {"controller": target, "generation": entry.generation,
			"placed_tick": entry.placed_tick, "method": entry.method}
		if entry.registration > 0:
			instance.registration = entry.registration
		if active:
			restored[entry.path] = instance
		targets[identity(entry.path, entry.generation)] = target
	var aliases := {}
	for name: String in snapshot.aliases:
		var key: Variant = snapshot.aliases[name]
		if key != null and (not key is String or not targets.has(key) or not targets[key] is AiControllerHost.Projectile):
			return {"error": "Unresolved projectile alias: " + name}
		aliases[name] = weakref(targets[key]) if key != null else WeakRef.new()
	return {"instances": restored, "targets": targets, "aliases": aliases,
		"display_tick": snapshot.display_tick, "next_generation": snapshot.next_generation}


static func commit(host: AiControllerHost, prepared: Dictionary) -> void:
	# The transaction owner restores fighter playheads/fields and the shared
	# registry as well, before dispatching anything. No source callbacks run here.
	assert(not prepared.has("error"))
	host.instances._instances = prepared.instances
	host.instances._next_generation = prepared.next_generation
	host.display_tick = prepared.display_tick
	host.fighter.source_projectiles = prepared.aliases


static func _controller_fields(controller: RefCounted) -> Array[String]:
	var fields: Array[String] = []
	for property in controller.get_property_list():
		if int(property.usage) & PROPERTY_USAGE_SCRIPT_VARIABLE and property.name != "adapter":
			fields.append(str(property.name))
	return fields


static func _projectile_state(target: RefCounted) -> Dictionary:
	return {"model": target.model.duplicate(true), "last_advance_tick": target.last_advance_tick,
		"instance_name": target.instance_name, "pending_natural_frames": Array(target.pending_natural_frames)}
