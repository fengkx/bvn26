extends RefCounted

# Local rollback checkpoints. Script objects are rebuilt; native scene nodes are
# retained by the owning battle until the last referencing checkpoint expires.
# The value graph preserves dictionary/array identity as well as object links.
const State = preload("res://simulation_state.gd")
const SessionState = preload("res://online_session_state.gd")
const IMMUTABLE := ["_timeline", "_fighter", "_definitions", "_assets", "_frames",
	"_combat", "spec", "_spec", "_hooks", "clips_metadata",
	"cpu_visual_spec", "cpu_profile", "ko_metadata", "_sound_assets", "_sound_segments",
	"_events", "_sound_events", "_manifest", "_scalar_fields", "_data", "_entries_by_label", "ai_color_operations", "training_spec", "_source_spec", "_helper_spec"]
const MAIN_FIELDS := ["game_world", "naruto", "ichigo", "current_world", "naruto_energy",
	"ichigo_energy", "combo_hud", "black_mu", "ts_face", "countdown", "timeout_timeline",
	"timeout_clip", "nextfight_from_timeout", "_source_nextfight_goto_phase", "_intro_just_finished",
	"pause_menu", "health_hud", "stage_background", "battle_intro", "source_random", "source_clock",
	"selected_stage", "opponent_driver", "opponent_input_context", "cpu_services", "cpu_stage_registry",
	"ko_timeline", "ko_clip", "ko_state", "ko_active", "ko_paused", "ko_menu_enabled",
	"ko_terminal_pending", "ko_nextfight_timer", "ko_interval_sequence", "match_input", "_match_inputs",
	"_match_input_active", "session", "super_runtime", "super_presentation", "physics_tick",
	"naruto_helper", "ichigo_helper", "screen_flash", "screen_flash_age", "hit_fx_pause_count",
	"player_body_driver", "source_callbacks", "source_health_rules", "source_health_registration",
	"source_frame_sequence", "source_child_frames", "player_body_services", "training_timer"]
const MAIN_EXTERNAL := [
	"tick_label",
	"state_label",
	"config_label",
	"fight_hud",
	"title_menu",
	"key_settings",
	"config_menu",
	"character_selection",
	"map_selection",
	"stage_sound",
	"cpu_profile",
	"cpu_visual_spec",
	"cpu_unresolved_services",
	"ko_recorded_timers",
	"ko_metadata",
	"input_recording_path",
	"diagnostics",
	"_diagnostic_initial_players",
	"_diagnostic_progress_signature",
	"_diagnostic_last_progress_ms",
	"_diagnostic_watchdog_elapsed_ms",
	"_diagnostic_stall_reported",
	"diagnostic_input_provider",
	"recorded_training_timers",
]
const EXTERNAL_FIELDS := ["diagnostics", "diagnostic_runtime"]
const FIELD_MODE_IMMUTABLE := 1
const FIELD_MODE_FIGHTER_SOURCE := 2
const FIELD_MODE_HUD_SPEC := 4
const FIELD_MODE_KO_IMMUTABLE := 8
const FIELD_MODE_HUD_IMMUTABLE := 16
const FIELD_MODE_SENSES_IMMUTABLE := 32
# Keep caller-side scalar bypasses identical to _encode's value-only fast path.
const DIRECT_SCALAR_BUILTINS := [TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING]
var error := ""
var _game: Node
var _records: Array = []
var _values: Array = []
var _objects := {}
var _container_buckets := {}
var profile := {"saves": 0, "encode_us": 0, "pack_us": 0, "retains_us": 0}
var _constants := {}
var _script_names := {}
var _field_descriptors := {}
var _script_signal_names := {}
var _immutable_fields := {}
var _placement_tables := {}
var _placements := {}
var _empty_array_prototypes := {}
var _empty_dictionary_prototypes := {}
var _constant_values: Array = []
var _constant_keys: Array[String] = []
var _snapshots := {}
var _snapshot_frames := {}
var _snapshot_graphs := {}
var _weak: Array = []
var _restored: Array = []
var _retired := {}
var _sounds := {}
var published_sounds := 0
var suppressed_sounds := 0

func configure(game: Node) -> void:
	_game = game
	_game.set_meta("rollback_owner", self)
	for path in ["ai_controller_host", "player_body_driver", "ko_timeline", "match_countdown", "source_body_callbacks"]:
		_register_script(load("res://" + path + ".gd"), "res://" + path + ".gd")

func save_state() -> Dictionary:
	error = ""
	var started := Time.get_ticks_usec()
	_records = []
	_values = []
	_objects = {}
	_container_buckets = {}
	_weak = []
	_encode(_game)
	# Children with callbacks may not have any strong script-field owner.
	for child in _game.game_world.get_children():
		if child is HitEffectRuntime or child is StageHitRuntime or child is ShadowSnapshot:
			_encode(child)
	var index := 0
	while index < _weak.size():
		var item: Array = _weak[index]
		var target: Object = item[1].get_ref()
		# Weak references never promote otherwise dead source instances.
		item[0]["target"] = _objects.get(target.get_instance_id(), -1) if target != null else -1
		index += 1
	if not error.is_empty():
		_values.clear()
		_weak.clear()
		_container_buckets.clear()
		return {"error": error}
	profile.encode_us += Time.get_ticks_usec() - started
	started = Time.get_ticks_usec()
	var snapshot := State.pack_state(State.BINARY_GRAPH_BUILD, _game.physics_tick, {"graph": var_to_bytes(_records)})
	if snapshot.has("error"):
		return snapshot
	var key := _snapshot_key(snapshot)
	var nodes := {}
	for id in _values.size():
		if _values[id] is Node:
			nodes[id] = _values[id]
	if _snapshot_graphs.has(key) and _snapshot_graphs[key] != snapshot.owners.graph:
		return {"error": "Local checkpoint index collision"}
	_snapshot_graphs[key] = snapshot.owners.graph
	_snapshots[key] = nodes
	_snapshot_frames[key] = snapshot.frame
	# Never keep RefCounted instances alive merely because they were snapshotted.
	_values.clear()
	_weak.clear()
	_container_buckets.clear()
	profile.pack_us += Time.get_ticks_usec() - started
	profile.saves += 1
	return snapshot

func validate_state(snapshot: Dictionary) -> String:
	var problem: String = State.validate_snapshot(snapshot, State.BINARY_GRAPH_BUILD, ["graph"])
	if not problem.is_empty():
		return problem
	if not snapshot.owners.graph is PackedByteArray:
		return "Invalid battle graph encoding"
	var key := _snapshot_key(snapshot)
	if not _snapshots.has(key) or _snapshot_graphs[key] != snapshot.owners.graph:
		return "Checkpoint is not retained by this battle"
	if _snapshot_frames[key] != snapshot.frame:
		return "Checkpoint frame mismatch"
	for node in _snapshots[key].values():
		if not is_instance_valid(node) or node.is_queued_for_deletion():
			return "Checkpoint node was destroyed"
	return ""

func load_state(snapshot: Dictionary) -> String:
	var problem := validate_state(snapshot)
	if not problem.is_empty():
		return problem
	var records_value: Variant = bytes_to_var(snapshot.owners.graph)
	problem = _validate_graph_records(records_value)
	if not problem.is_empty(): return problem
	var records: Array = records_value
	# KO clip dictionaries own their dispatch objects, which in turn reference
	# the dictionaries. Break the outgoing graph before replacing its roots.
	for timeline in [_game.ko_timeline, _game.timeout_timeline]:
		if timeline != null: timeline.unbind_registry()
	_immutable_fields.clear()
	var nodes: Dictionary = _snapshots[_snapshot_key(snapshot)]
	_restored = []
	for id in records.size():
		var record: Dictionary = records[id]
		match record.kind:
			"array": _restored.append(_constants[record.prototype].duplicate())
			"dictionary": _restored.append(_constants[record.prototype].duplicate())
			"node": _restored.append(nodes[id])
			"rng": _restored.append(RandomNumberGenerator.new())
			"object":
				var script: Script = _constants[record.script]
				var args := []
				for method in script.get_script_method_list():
					if method.name == "_init":
						for arg in method.args.slice(0, method.args.size() - method.default_args.size()):
							args.append({} if arg.type == TYPE_DICTIONARY else null)
				_restored.append(script.new.callv(args))
	if _game.ko_nextfight_timer != null and _game.ko_nextfight_timer not in nodes.values():
		retire(_game.ko_nextfight_timer)
	for child in _game.game_world.get_children():
		if (child is HitEffectRuntime or child is StageHitRuntime or child is ShadowSnapshot) and child not in nodes.values():
			retire(child)
	for id in records.size():
		if records[id].kind == "node" and records[id].parent != null:
			var node: Node = _restored[id]
			if node.get_parent() == null:
				_decode(records[id].parent).add_child(node)
			node.get_parent().move_child(node, mini(records[id].order, node.get_parent().get_child_count() - 1))
			_retired.erase(node.get_instance_id())
	# Populate containers first, then all references see the same backing values.
	for id in records.size():
		var record: Dictionary = records[id]
		if record.kind in ["array", "dictionary"]:
			_restored[id].clear()
			if record.kind == "array":
				for entry in record.entries: _restored[id].append(_decode(entry))
			else:
				for entry_index in range(0, record.entries.size(), 2):
					_restored[id][_decode(record.entries[entry_index])] = _decode(record.entries[entry_index + 1])
	for id in records.size():
		var record: Dictionary = records[id]
		var target: Variant = _restored[id]
		if record.kind == "rng":
			target.seed = record.seed
			target.state = record.state
		elif record.kind in ["object", "node"]:
			if id == 0 and record.has("session_causal"):
				var session_problem := SessionState.restore(_game.session, _decode(record.session_causal))
				if not session_problem.is_empty():
					return session_problem
			if record.has("hud_placement"):
				target.spec.placement = _decode(record.hud_placement)
			for field in record.fields:
				target.set(field, _decode(record.fields[field]))
			if record.kind == "node":
				if record.has("flash"):
					var flash: Array = _decode(record.flash)
					target.material.set_shader_parameter("tint", flash[0])
					target.material.set_shader_parameter("opacity", flash[1])
				for field in record.native:
					target.set(field, _decode(record.native[field]))
				for key in target.get_meta_list():
					if str(key) == "shadow_counter": target.remove_meta(key)
				for key in record.meta: target.set_meta(key, _decode(record.meta[key]))
	# Reconnect script signals because their targets may be rebuilt controllers.
	for id in records.size():
		var record: Dictionary = records[id]
		if record.kind not in ["object", "node"]: continue
		var target: Object = _restored[id]
		for signal_name in record.signals:
			for connection in target.get_signal_connection_list(signal_name):
				target.disconnect(signal_name, connection.callable)
			for connection in record.signals[signal_name]:
				target.connect(signal_name, _decode(connection.callback), connection.flags)
	for target in _restored:
		if target is TimelinePreview and target.is_inside_tree():
			target.refresh_checkpoint_display()
	_restored.clear()
	_placement_tables.clear()
	_placements.clear()
	return ""

func _constant(value: Variant) -> String:
	# These are immutable resources/configuration, never mutable battle state.
	var key: String
	if value is Resource:
		key = value.resource_path
		if key.is_empty():
			if value is Script and _script_names.has(value.get_instance_id()):
				key = _script_names[value.get_instance_id()]
			elif value is Shader:
				key = "shader:" + value.code.sha256_text()
			elif value is AtlasTexture:
				key = "atlas:%s:%s:%s" % [_constant(value.atlas), value.region, value.margin]
			else:
				error = "Unidentified immutable resource: " + value.get_class()
	elif value is Callable:
		key = str(value.hash())
	else:
		if value is Array or value is Dictionary:
			for i in _constant_values.size():
				if is_same(value, _constant_values[i]): return _constant_keys[i]
		key = var_to_bytes(value).hex_encode().sha256_text()
		if value is Array:
			var type_key := _array_type_key(value)
			key = "array:" + type_key if value.is_empty() else key + ":" + type_key
	if _constants.has(key): return key
	_constants[key] = value
	if (value is Array or value is Dictionary) and not value.is_empty():
		_constant_values.append(value)
		_constant_keys.append(key)
	return key

func _encode(value: Variant) -> Variant:
	if value is GameSession:
		_constants["external:session"] = value
		return {"constant": "external:session"}
	if typeof(value) in DIRECT_SCALAR_BUILTINS or (value is float and is_finite(value)):
		return value
	if value is Callable:
		if value.is_null(): return {"empty_callable": true}
		if not value.is_valid():
			error = "Invalid pending callable"
			return null
		var target: Object = value.get_object()
		if not target.has_method(value.get_method()):
			error = "Anonymous callbacks cannot be restored: " + str(value.get_method())
			return null
		return {"callable": _encode(target), "method": str(value.get_method()),
			"args": _encode(value.get_bound_arguments()), "unbound": value.get_unbound_arguments_count()}
	if value is WeakRef:
		var result := {"weak": true, "target": -1}
		_weak.append([result, value])
		return result
	if value is Resource:
		return {"constant": _constant(value)}
	if value is Array or value is Dictionary:
		var bucket_key: int = hash(value)
		if value is Dictionary:
			for placement in _placements.get(bucket_key, []):
				if is_same(placement[0], value): return {"constant": placement[1]}
		for entry in _container_buckets.get(bucket_key, []):
			if is_same(value, entry[0]): return {"ref": entry[1]}
		var id := _records.size()
		if not _container_buckets.has(bucket_key): _container_buckets[bucket_key] = []
		_container_buckets[bucket_key].append([value, id])
		var record := {"kind": "array" if value is Array else "dictionary", "prototype": _empty_prototype_key(value), "entries": []}
		_records.append(record)
		_values.append(value)
		if value is Array:
			for entry in value:
				record.entries.append(entry if typeof(entry) in DIRECT_SCALAR_BUILTINS or (entry is float and is_finite(entry)) else _encode(entry))
		else:
			for key in value:
				record.entries.append(key if typeof(key) in DIRECT_SCALAR_BUILTINS or (key is float and is_finite(key)) else _encode(key))
				var item: Variant = value[key]
				record.entries.append(item if typeof(item) in DIRECT_SCALAR_BUILTINS or (item is float and is_finite(item)) else _encode(item))
		return {"ref": id}
	if value is Object:
		if not is_instance_valid(value): return null
		if _objects.has(value.get_instance_id()): return {"ref": _objects[value.get_instance_id()]}
		var id := _records.size()
		_objects[value.get_instance_id()] = id
		var record := {"kind": "node" if value is Node else "object", "fields": {}, "signals": {}}
		_records.append(record)
		_values.append(value)
		if value is RandomNumberGenerator:
			record.merge({"kind": "rng", "seed": value.seed, "state": value.state}, true)
			return {"ref": id}
		if value is KoTimeline: _register_placements(value)
		var script: Script = value.get_script()
		if script != null:
			record.script = _constant(script)
			if not _field_descriptors.has(script):
				_field_descriptors[script] = _build_field_descriptors(value)
			for descriptor in _field_descriptors[script]:
				var field: String = descriptor[0]
				var field_mode: int = descriptor[1]
				var contents: Variant = value.get(field)
				if value == _game and field not in MAIN_FIELDS:
					if field not in MAIN_EXTERNAL: error = "Unaudited Main field: " + field
					continue
				if field in EXTERNAL_FIELDS: continue
				if value == _game and field == "session":
					var binding := "external:session"
					_constants[binding] = contents
					record.fields[field] = {"constant": binding}
					var session_state := SessionState.capture(contents)
					if session_state.has("error"):
						error = session_state.error
					else:
						record.session_causal = _encode(session_state)
					continue
				if value == _game.match_input and field in ["source", "intro_source"]:
					var binding := "external:match_input." + field
					_constants[binding] = value.get(field)
					record.fields[field] = {"constant": binding}
					continue
				if (field_mode & FIELD_MODE_FIGHTER_SOURCE) != 0 and value is FighterRuntime: continue
				if (field_mode & FIELD_MODE_HUD_SPEC) != 0 and value is HealthHud:
					record.hud_placement = {"constant": _constant(value.spec.placement)}
					continue
				var immutable_field := (field_mode & FIELD_MODE_IMMUTABLE) != 0
				if not immutable_field and (field_mode & FIELD_MODE_KO_IMMUTABLE) != 0 and value is KoTimeline:
					immutable_field = true
				if not immutable_field and (field_mode & FIELD_MODE_HUD_IMMUTABLE) != 0 and value is HealthHud:
					immutable_field = true
				if not immutable_field and (field_mode & FIELD_MODE_SENSES_IMMUTABLE) != 0 and value is AiSenses:
					immutable_field = true
				if immutable_field and (contents is Dictionary or contents is Array) and not (value is HealthHud and field == "spec"):
					var instance_id: int = value.get_instance_id()
					if not _immutable_fields.has(instance_id): _immutable_fields[instance_id] = {}
					var instance_fields: Dictionary = _immutable_fields[instance_id]
					if not instance_fields.has(field) or not is_same(instance_fields[field][0], contents):
						instance_fields[field] = [contents, _constant(contents)]
					record.fields[field] = {"constant": instance_fields[field][1]}
				else:
					record.fields[field] = contents if typeof(contents) in DIRECT_SCALAR_BUILTINS or (contents is float and is_finite(contents)) else _encode(contents)
			var signal_names: Array
			if _script_signal_names.has(script):
				signal_names = _script_signal_names[script]
			else:
				signal_names = []
				for item in script.get_script_signal_list(): signal_names.append(item.name)
				_script_signal_names[script] = signal_names
			for signal_name in signal_names:
				var connections := []
				for connection in value.get_signal_connection_list(signal_name):
					connections.append({"callback": _encode(connection.callable), "flags": connection.flags})
				record.signals[str(signal_name)] = connections
		elif not value is Node:
			error = "Unsupported native object: " + value.get_class()
		if value is Node:
			if value.get_class() not in ["Node", "Node2D", "Sprite2D", "Timer", "ColorRect", "Control", "SubViewport"]:
				error = "Unaudited native node: " + value.get_class()
			if value is Timer and not value.is_stopped(): error = "Live timer in checkpoint"
			record.parent = _encode(value.get_parent()) if value is HitEffectRuntime or value is StageHitRuntime or value is ShadowSnapshot or value == _game.ko_nextfight_timer else null
			record.order = value.get_index() if value.get_parent() != null else 0
			record.native = {}
			record.meta = {}
			if value == _game.screen_flash:
				record.flash = _encode([value.material.get_shader_parameter("tint"), value.material.get_shader_parameter("opacity")])
			if value is Node2D:
				for field in ["position", "rotation", "scale", "skew", "visible", "modulate", "self_modulate", "z_index"]:
					record.native[field] = _encode(value.get(field))
			if value is Timer:
				for field in ["wait_time", "one_shot"]: record.native[field] = _encode(value.get(field))
			if value is Sprite2D:
				for field in ["texture", "frame", "offset"]:
					if field == "texture" and value.get_parent() is ShadowSnapshot: continue
					record.native[field] = _encode(value.get(field))
			if value is Control:
				for field in ["visible", "modulate"]: record.native[field] = _encode(value.get(field))
			if value.has_meta("shadow_counter"): record.meta.shadow_counter = _encode(value.get_meta("shadow_counter"))
		return {"ref": id}
	if typeof(value) in [TYPE_RID, TYPE_SIGNAL]:
		error = "Non-value native handle in checkpoint"
		return null
	# Native scalar types (including packed arrays) use Godot's value-only codec.
	if typeof(value) in DIRECT_SCALAR_BUILTINS or (value is float and is_finite(value)):
		return value
	return {"value": var_to_bytes(value).hex_encode()}

func _decode(value: Variant) -> Variant:
	if not value is Dictionary: return value
	if value.has("ref"): return _restored[value.ref]
	if value.has("constant"): return _constants[value.constant]
	if value.has("value"): return bytes_to_var(value.value.hex_decode())
	if value.has("empty_callable"): return Callable()
	if value.has("weak"): return weakref(_restored[value.target]) if value.target >= 0 else WeakRef.new()
	if value.has("callable"):
		var callback := Callable(_decode(value.callable), value.method).bindv(_decode(value.args))
		return callback.unbind(value.unbound) if value.unbound > 0 else callback
	return null

func _validate_graph_records(value: Variant) -> String:
	if not value is Array: return "Invalid battle graph records"
	for record in value:
		if not record is Dictionary: return "Invalid battle graph record"
		if record.get("kind") == "dictionary":
			var entries: Variant = record.get("entries")
			if not entries is Array or entries.size() % 2 != 0:
				return "Invalid dictionary graph entries"
	return ""

func _build_field_descriptors(value: Object) -> Array:
	var descriptors: Array = []
	for property in value.get_property_list():
		if not property.usage & PROPERTY_USAGE_SCRIPT_VARIABLE: continue
		var field: String = property.name
		var mode := 0
		if field in IMMUTABLE: mode |= FIELD_MODE_IMMUTABLE
		if field == "source_x" or field == "source_y": mode |= FIELD_MODE_FIGHTER_SOURCE
		if field == "spec": mode |= FIELD_MODE_HUD_SPEC
		if field in ["clips", "methods", "callbacks", "load_callbacks"]: mode |= FIELD_MODE_KO_IMMUTABLE
		if field == "portraits": mode |= FIELD_MODE_HUD_IMMUTABLE
		if field == "placement" or field == "sensors": mode |= FIELD_MODE_SENSES_IMMUTABLE
		descriptors.append([field, mode])
	return descriptors

func _array_type_key(value: Array) -> String:
	var typed_script: Script = value.get_typed_script()
	return "%s:%s:%s" % [value.get_typed_builtin(), value.get_typed_class_name(), _constant(typed_script) if typed_script != null else ""]

func _empty_prototype_key(value: Variant) -> String:
	if value is Array:
		var signature := _array_type_key(value)
		if _empty_array_prototypes.has(signature): return _empty_array_prototypes[signature]
		var prototype: Array = value.duplicate()
		prototype.clear()
		var prototype_key := _constant(prototype)
		_empty_array_prototypes[signature] = prototype_key
		return prototype_key
	var dictionary: Dictionary = value
	var typed_key := dictionary.is_typed_key()
	var typed_value := dictionary.is_typed_value()
	var signature: Array = [typed_key]
	if typed_key:
		var key_script: Script = dictionary.get_typed_key_script()
		signature.append(dictionary.get_typed_key_builtin())
		signature.append(dictionary.get_typed_key_class_name())
		signature.append(_constant(key_script) if key_script != null else "")
	signature.append(typed_value)
	if typed_value:
		var value_script: Script = dictionary.get_typed_value_script()
		signature.append(dictionary.get_typed_value_builtin())
		signature.append(dictionary.get_typed_value_class_name())
		signature.append(_constant(value_script) if value_script != null else "")
	var cache: Dictionary = _empty_dictionary_prototypes
	for part in signature:
		if not cache.has(part): cache[part] = {}
		cache = cache[part]
	if cache.has("prototype_key"): return cache["prototype_key"]
	var prototype: Dictionary = dictionary.duplicate()
	prototype.clear()
	var prototype_key := _constant(prototype)
	cache["prototype_key"] = prototype_key
	return prototype_key

func retire(node: Node) -> void:
	_retired[node.get_instance_id()] = node
	if node.get_parent() != null:
		node.get_parent().remove_child(node)

func close() -> void:
	_values.clear()
	_weak.clear()
	_container_buckets.clear()
	_game.remove_meta("rollback_owner")
	for node in _retired.values():
		if is_instance_valid(node): node.free()
	_retired.clear()
	_snapshots.clear()
	_snapshot_frames.clear()
	_snapshot_graphs.clear()
	_sounds.clear()
	_constants.clear()
	_script_signal_names.clear()
	_field_descriptors.clear()
	_immutable_fields.clear()
	_empty_array_prototypes.clear()
	_empty_dictionary_prototypes.clear()
	_placement_tables.clear()
	_placements.clear()
	_constant_values.clear()
	_constant_keys.clear()

func allow_sound(node: Node, event: String) -> bool:
	var identity := str(node.get_path())
	if node is TimelinePreview:
		identity = node.fighter_directory + ":" + str(node.get("player_slot"))
		if node is HelperRuntime and node.owner_fighter != null:
			identity += ":" + node.owner_fighter.player_slot
		if node is StageHitRuntime:
			identity += ":" + node.caster.player_slot + ":" + node.source_name
	elif node is HitEffectRuntime:
		identity = node._directory
	var key := "%d:%s:%s" % [_game.physics_tick, identity, event]
	if _sounds.has(key):
		suppressed_sounds += 1
		return false
	_sounds[key] = _game.physics_tick
	published_sounds += 1
	return true

func retain_states(states: Array) -> void:
	var started := Time.get_ticks_usec()
	var oldest: int = _game.physics_tick
	for state in states: oldest = mini(oldest, state.frame)
	for key in _snapshot_frames.keys():
		if _snapshot_frames[key] < oldest:
			_snapshot_frames.erase(key)
			_snapshot_graphs.erase(key)
			_snapshots.erase(key)
	var retained_nodes := {}
	for nodes in _snapshots.values():
		for node in nodes.values(): retained_nodes[node.get_instance_id()] = true
	for id in _retired.keys():
		if not retained_nodes.has(id):
			_retired[id].free()
			_retired.erase(id)
	for key in _sounds.keys():
		if _sounds[key] < oldest: _sounds.erase(key)
	for instance_id in _immutable_fields.keys():
		if not is_instance_id_valid(int(instance_id)): _immutable_fields.erase(instance_id)
	profile.retains_us += Time.get_ticks_usec() - started

func _register_script(script: Script, identity: String) -> void:
	_script_names[script.get_instance_id()] = identity
	for key in script.get_script_constant_map():
		var child: Variant = script.get_script_constant_map()[key]
		if child is Script and child.resource_path.is_empty():
			_register_script(child, identity + "::" + str(key))

func _register_placements(timeline: KoTimeline) -> void:
	if _placement_tables.has(timeline.get_instance_id()): return
	_placement_tables[timeline.get_instance_id()] = true
	var root_key := _constant(timeline.clips)
	var canonical: Dictionary = _constants[root_key]
	for symbol in timeline.clips:
		var frames: Array = timeline.clips[symbol].frames
		for frame in frames.size():
			for index in frames[frame].size():
				var placement: Dictionary = frames[frame][index]
				var key := "placement:%s:%s:%d:%d" % [root_key, symbol, frame, index]
				_constants[key] = canonical[symbol].frames[frame][index]
				var bucket: int = hash(placement)
				if not _placements.has(bucket): _placements[bucket] = []
				_placements[bucket].append([placement, key])

func _snapshot_key(snapshot: Dictionary) -> String:
	return "%d:%d" % [snapshot.frame, hash(snapshot.owners.graph)]
