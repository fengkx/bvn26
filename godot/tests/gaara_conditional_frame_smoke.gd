extends SceneTree


class FollowFighter extends FighterRuntime:
	func named_instance_origin(_instance_name: String) -> Vector2:
		return Vector2(10, 20)

	func refresh_display() -> void:
		pass


class Context extends AiPredicateContext:
	var health := 1000
	var action := 0
	var shown := true

	func read_field(key: String) -> Variant:
		match key:
			"opponent_hp": return health
			"opponent_action": return action
			"opponent_visible": return shown
		assert(false)
		return null

	func write_field(key: String, value: Variant) -> void:
		assert(key == "opponent_visible")
		shown = value


class Controller extends AiControllerHost:
	var destinations: Array = []

	func goto_label(label: String, play: bool) -> void:
		destinations.append([label, play])


func _initialize() -> void:
	var fighter := FollowFighter.new()
	var context := Context.new(fighter)
	fighter.ai_predicate_context = context
	var driver := AiCpuDriver.new()
	driver.fighter = fighter
	var controller := Controller.new()
	driver.controller = controller
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/gaara/ai.json"))
	# The source hides only a living, hurt target; every other case takes the else.
	for sample in [[1000, -1, false], [0, -1, true], [1000, 0, true]]:
		context.health = sample[0]
		context.action = sample[1]
		context.shown = true
		controller.destinations.clear()
		driver._frame_service(spec.frame_calls["519"][0])
		assert(context.shown == sample[2])
		assert(controller.destinations == ([["必杀1", false]] if sample[2] else []))
		controller.destinations.clear()
		driver._frame_service(spec.frame_calls["865"][0])
		assert(controller.destinations == ([["超必杀1", false]] if sample[2] else []))
	var opponent := FighterRuntime.new()
	fighter.opponent = opponent
	fighter.source_x = 300
	fighter.source_y = 200
	opponent.source_y = 250
	var follow: Dictionary = spec.frame_calls["501"][0].duplicate(true)
	follow["place_y"] = true
	# lockx guards only X; Y still follows when the target is behind or level.
	for sample in [[1, 350, 40], [1, 250, 7], [-1, 250, 40], [-1, 350, 7], [1, 300, 7]]:
		fighter.scale.x = sample[0]
		fighter.facing = -int(sample[0])
		opponent.source_x = sample[1]
		fighter.set_instance_local_offset("bs1atm", Vector2(7, 8))
		driver._frame_service(follow)
		assert(fighter.instance_local_offset("bs1atm") == Vector2(sample[2], 30))
	opponent.free()
	driver.free()
	fighter.free()
	print("GAARA_CONDITIONAL_FRAME_SMOKE_OK alive_hurt=hide else=miss visible=skip")
	quit()
