extends Node

var fighter: FighterRuntime
var body: RefCounted
var context: Context
var controller: AiControllerHost
var _driver: AiCpuDriver
var tick: int = 0


class Context extends AiBodyContext:
	var inputs: Dictionary = {}

	func source_key(key: String) -> bool:
		var mapping := {"左": "left", "右": "right", "上": "up", "下": "down",
			"斩": "attack", "跳": "jump", "冲": "dash", "招": "ranged",
			"必杀": "special", "换": "summon"}
		assert(mapping.has(key), "Uncompiled player key: " + key)
		return inputs.get(mapping[key], false)


func configure(actor: FighterRuntime, directory: String, platforms: Dictionary,
		floor_y: float, map_width: float, services: Callable,
		registry: SourceCallbackRegistry = null) -> void:
	fighter = actor
	context = Context.new(actor)
	context.use_ai = false
	_driver = AiCpuDriver.new()
	add_child(_driver)
	_driver.body_replaced.connect(_on_body_replaced)
	_driver.configure(actor, directory, platforms, floor_y, map_width,
		{"touchFloor": null}, services, false, registry, context)
	body = _driver.body
	controller = _driver.controller
	controller.context.use_ai = false
	controller.key_reader = context.source_key
	fighter.source_body = body
	_driver.begin_display_tick(tick)


func begin_tick(display_tick: int, inputs: Dictionary) -> void:
	tick = display_tick
	context.inputs = inputs if inputs.is_read_only() else inputs.duplicate()
	_driver.prepare_display_tick(tick)


func advance_timeline() -> void:
	_driver.advance_timeline()


func prepare_callbacks() -> void:
	_driver.begin_display_tick(tick)


func prepare_frame_actions(count: int) -> void:
	_driver.initial_frame_count = count


func stop() -> void:
	if fighter == null:
		return
	fighter.source_body = null
	_driver.stop()
	_driver.queue_free()
	_driver = null
	context.body_target = null
	context.fighter = null
	body.adapter = null
	body = null
	context = null
	controller = null
	fighter = null


func _exit_tree() -> void:
	stop()


func _on_body_replaced() -> void:
	body = _driver.body
	controller = _driver.controller
	context = _driver.body_context


func configure_forms(profiles: Dictionary, intervals: SourceRootIntervals,
		root_values: Dictionary, parent_frame: int = 1) -> void:
	_driver.configure_forms(profiles, intervals, root_values, parent_frame)
