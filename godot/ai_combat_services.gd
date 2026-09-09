class_name AiCombatServices
extends RefCounted

var fighter: FighterRuntime
var super_runtime: SuperRuntime
var helpers: Array = []
var stage_registry: StageHitRegistry
var effect_parent: Node2D
var remaining_services: Callable
var stage_effects: Array[StageHitRuntime] = []
var stage_lookup_order: Array = []


func invoke(name: String, args: Array) -> Variant:
	match name:
		"frame_super":
			_apply_super(args[0])
		"receive":
			assert(args[0] in ["beida", "fangyu"])
			fighter.guarding = args[0] == "fangyu"
			var opponent_helper: HelperRuntime = null
			for helper: HelperRuntime in helpers:
				if helper.owner_fighter == fighter.opponent:
					opponent_helper = helper
					break
			return CombatResolver.resolve_incoming(fighter, fighter.opponent,
				opponent_helper, stage_registry, stage_lookup_order)
		"bsd":
			_apply_super({"op": "super_start", "kind": "bsd", "xg": args[0],
				"helper": args[1]})
		"bsw":
			# The fighter BODY calls this with fz=false; helper release is separate.
			assert(args[0] == false)
			_apply_super({"op": "super_end", "kind": "bsw"})
		"addStgHit":
			var directory := "res://generated/effects/" + str(args[0])
			assert(FileAccess.file_exists(directory.path_join("stage_hit.json")),
				"Stage hit requires compiled source metadata: " + str(args[0]))
			var effect := StageHitRuntime.new()
			effect.configure(directory, fighter, args[1])
			effect_parent.add_child(effect)
			stage_registry.register(effect)
			stage_effects.append(effect)
		_:
			assert(remaining_services.is_valid(), "Unconnected AI effect service: " + name)
			return remaining_services.call(name, args)
	return null


func _apply_super(event: Dictionary) -> void:
	super_runtime.apply(event, fighter, fighter.opponent, helpers)
	for actor: FighterRuntime in [fighter, fighter.opponent]:
		actor.ai_source_state.values["bs"] = actor.bs


func advance_stage_timelines() -> void:
	for effect in stage_effects:
		if is_instance_valid(effect):
			effect.advance_timeline()


func run_stage_frames() -> void:
	for index in range(stage_effects.size() - 1, -1, -1):
		var effect := stage_effects[index]
		if not is_instance_valid(effect):
			stage_effects.remove_at(index)
			continue
		effect.run_frame_actions()
		if effect.expired:
			stage_registry.forget(effect)
			stage_effects.remove_at(index)


func clear() -> void:
	for effect in stage_effects:
		if is_instance_valid(effect):
			stage_registry.forget(effect)
			effect.queue_free()
	stage_effects.clear()
	remaining_services = Callable()
	fighter = null
	super_runtime = null
	helpers.clear()
	effect_parent = null
	stage_registry = null
	stage_lookup_order.clear()
