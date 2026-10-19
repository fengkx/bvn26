class_name AiPredicateContext
extends RefCounted

var fighter: FighterRuntime
var helper_action: Variant = null
var gravity: float = 10.0
var use_ai: Variant = true


func _init(owner_fighter: FighterRuntime) -> void:
	fighter = owner_fighter


func read_field(key: String) -> Variant:
	match key:
		"useAI": return use_ai
		"x": return fighter.source_x
		"y": return fighter.source_y
		"scale_X": return fighter.facing
		"xscale": return fighter.scale.x * 100.0
		"ql": return fighter.energy
		"root_paused": return fighter.root_zhanting
		"gravity": return gravity
		"opponent_x": return fighter.opponent.source_x if fighter.opponent != null else null
		"opponent_y": return fighter.opponent.source_y if fighter.opponent != null else null
		"opponent_visible": return fighter.opponent.visible if fighter.opponent != null else null
		"opponent_hp": return fighter.opponent.health if fighter.opponent != null else null
		"opponent_action":
			return fighter.opponent.ai_source_state.read_field("动作") if fighter.opponent != null else null
		"opponent_sw":
			return fighter.opponent.ai_source_state.read_field("sw") if fighter.opponent != null else null
		"opponent_helper_action": return helper_action
		"attran", "defran", "goran", "jumpran", "bisharan", "touchFloor", "canhit", "sw", "speed", "jumpPower", "jumped", "fall", "khit", "touch":
			return fighter.ai_source_state.read_field(key)
	# Source conditions may refer to a field declared by this timeline (for
	# example Cbshit). Keep the lookup generic so new source fields do not need
	# role-specific branches in the runtime.
		_:
			if fighter.ai_source_state.values.has(key):
				return fighter.ai_source_state.read_field(key)
	assert(false, "Unmapped AI field: " + key)
	return null


func write_field(key: String, value: Variant) -> void:
	match key:
		"x": fighter.source_x = float(value)
		"y": fighter.source_y = float(value)
		"opponent_x": fighter.opponent.source_x = float(value)
		"opponent_y": fighter.opponent.source_y = float(value)
		"opponent_visible": fighter.opponent.visible = bool(value)
		"scale_X": fighter.facing = int(value)
		"xscale": fighter.scale.x = float(value) / 100.0
		"jumped", "fall", "khit", "touch": fighter.ai_source_state.values[key] = value
		_: assert(false, "Unmapped AI write: " + key)


func sensor_hit(key: String) -> Variant:
	if fighter.opponent == null:
		return null
	return fighter.ai_senses.hit(key, fighter.opponent)


func body_hit(key: String) -> Variant:
	if fighter.opponent == null:
		return null
	var own := fighter.instance_global_bounds(key)
	var target := fighter.opponent.instance_global_bounds("bdmn")
	if not own.has_area() or not target.has_area():
		return null
	return SourceHitTest.intersects(own, target)


func power_field(key: String) -> Variant:
	return fighter.ai_source_state.spec["base_power_fields"].get(key)
