class_name AiBodyContext
extends AiPredicateContext

const CoordinateStore = preload("res://source_coordinate.gd")

var controller_ref: WeakRef
var external_call: Callable
var source_platforms: Dictionary = {}
var root_wudi: Variant = false
var is_naruto: Variant = false
var map_size_x: float
var floor_y: float
var _scalar_fields: PackedStringArray
var timeout_scheduler: AiSourceTimeouts
var body_target: WeakRef


func configure(host: AiControllerHost, metadata: Dictionary, platforms: Dictionary) -> void:
	controller_ref = weakref(host)
	configure_source(metadata, platforms)


func configure_source(metadata: Dictionary, platforms: Dictionary) -> void:
	assert(metadata["swf_sha256"] == fighter.ai_source_state.spec["source_swf"]["sha256"])
	# chushi copies this flag from the selected fighter, for both slots.
	is_naruto = fighter._combat["is_naruto"]
	_scalar_fields = PackedStringArray(metadata["scalar_fields"])
	# Keys are authored ban indices, not positions in a compacted array.
	source_platforms = platforms.duplicate(true)


func read_field(key: String) -> Variant:
	match key:
		"hp": return fighter.health
		"vecx": return fighter.body_forward_velocity
		"heavy": return fighter.body_heavy
		"depth": return fighter.display_depth
		"opponent_vecx": return fighter.opponent.body_forward_velocity
		"opponent_heavy": return fighter.opponent.body_heavy
		"opponent_depth": return fighter.opponent.display_depth
		"opponent_xscale": return fighter.opponent.scale.x * 100.0
		"opponent_airBody": return fighter.opponent.ai_source_state.read_field("airBody")
		"root_wudi": return root_wudi
		"useAI": return use_ai
		"is_naruto": return is_naruto
		"modo": return fighter.modo
		"mapSizeX": return map_size_x
		"floorY": return floor_y
	if key in _scalar_fields and key != "ql":
		return fighter.ai_source_state.read_field(key)
	return super.read_field(key)


func write_field(key: String, value: Variant) -> void:
	match key:
		"hp": fighter.health = float(value)
		"ql": fighter.energy = float(value)
		"vecx": fighter.body_forward_velocity = float(value)
		"opponent_x": fighter.opponent.source_x = float(value)
		_:
			if key in _scalar_fields:
				fighter.ai_source_state.values[key] = value
			else:
				super.write_field(key, value)


func goto_label(label: String, play: bool) -> void:
	var host: AiControllerHost = controller_ref.get_ref()
	assert(host != null)
	host.goto_label(label, play)


func play_body() -> void:
	fighter.timeline_playing = true


func move_body(other: bool, axis: String, value: Variant) -> void:
	var target := fighter.opponent if other else fighter
	assert(target != null)
	if axis == "moveX":
		target.source_x += float(value) * target.facing
	elif axis == "moveY":
		target.source_y += float(value)
	else:
		assert(false, "Unknown BODY movement: " + axis)


func platform(index: Variant) -> Variant:
	return index if source_platforms.has(int(index)) else null


func platform_field(index: Variant, key: String) -> Variant:
	assert(source_platforms.has(int(index)))
	var bounds: Rect2 = source_platforms[int(index)]
	match key:
		"x": return CoordinateStore.from_projection(bounds.position.x)
		"y": return CoordinateStore.from_projection(bounds.position.y)
		"width": return bounds.size.x
	assert(false, "Unknown platform field: " + key)
	return null


func swap_depths() -> void:
	var depth := fighter.display_depth
	fighter.display_depth = fighter.opponent.display_depth
	fighter.opponent.display_depth = depth
	var visual_depth := fighter.z_index
	fighter.z_index = fighter.opponent.z_index
	fighter.opponent.z_index = visual_depth


func body_service(name: String) -> Variant:
	return _external(name, [])


func shadow(color: Dictionary) -> void:
	_external("showdow", [color])


func super_start(clip: String, option: bool) -> void:
	_external("bsd", [clip, option])


func super_end(option: bool) -> void:
	_external("bsw", [option])


func child_effect(clip: String, x: Variant, y: Variant) -> void:
	_external("addChildXG", [clip, x, y])


func stage_hit(clip: String, params: Dictionary) -> void:
	_external("addStgHit", [clip, params])


func defer_body(method: String, delay: Variant) -> void:
	if timeout_scheduler == null:
		_external("setTimeout", [method, delay])
		return
	var body: RefCounted = body_target.get_ref()
	assert(body != null and body.has_method(method))
	timeout_scheduler.schedule(Callable(body, method), int(delay))


func trace_init(mode: Variant, use_cpu: Variant) -> void:
	print("AI_INIT_WUDI ", mode, ",", use_cpu)


func _external(name: String, args: Array) -> Variant:
	assert(external_call.is_valid(), "Unconnected BODY service: " + name)
	return external_call.call(name, args)
