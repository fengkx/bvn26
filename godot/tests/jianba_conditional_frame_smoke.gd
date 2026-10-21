extends SceneTree


class Context extends AiPredicateContext:
	var health := 1000
	var action := 0
	var contact: Variant = false
	var queries := 0

	func read_field(key: String) -> Variant:
		assert(key in ["opponent_hp", "opponent_action"])
		return health if key == "opponent_hp" else action

	func body_hit(key: String) -> Variant:
		assert(key == "cbs0atm")
		queries += 1
		return contact


class Controller extends AiControllerHost:
	var destinations: Array = []

	func goto_label(label: String, play: bool) -> void:
		destinations.append([label, play])


func _initialize() -> void:
	var fighter := FighterRuntime.new()
	var context := Context.new(fighter)
	fighter.ai_predicate_context = context
	var driver := AiCpuDriver.new()
	driver.fighter = fighter
	var controller := Controller.new()
	driver.controller = controller
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/jianba/ai.json"))
	var event: Dictionary = spec.frame_calls["767"][0]
	# The source's early returns must also skip the collision query.
	for sample in [[0, -1, true, false, 0], [1000, -1, false, true, 0],
			[1000, 0, true, true, 1], [1000, 0, false, false, 1],
			[1000, 0, null, false, 1]]:
		context.health = sample[0]
		context.action = sample[1]
		context.contact = sample[2]
		context.queries = 0
		controller.destinations.clear()
		fighter.timeline_playing = false
		driver._frame_service(event)
		assert(context.queries == sample[4])
		assert(fighter.timeline_playing == sample[3])
		assert(controller.destinations == ([["超必杀1", false]] if sample[3] else []))
	driver.free()
	fighter.free()
	print("JIANBA_CONDITIONAL_FRAME_SMOKE_OK dead=halt hurt=short_circuit contact=required missing=false")
	quit()
