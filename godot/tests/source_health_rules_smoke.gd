extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighters: Array[FighterRuntime] = []
	for name in ["minren", "yihu"]:
		var fighter := FighterRuntime.new()
		fighter.fighter_directory = "res://generated/fighters/" + name
		root.add_child(fighter)
		fighters.append(fighter)
	var rules := preload("res://source_health_rules.gd").new()
	rules.configure(fighters, func() -> float: return 2000.0)
	fighters[0].health = 400
	fighters[1].health = 399
	fighters[0].energy = 0
	fighters[1].energy = 300
	fighters[0].root_zhanting = true
	fighters[1].root_zhanting = true
	rules.enter_frame()
	assert(fighters[0].energy == 0)
	assert(fighters[1].energy == 300.2)
	for slot in 2:
		fighters[slot].health = 0
		var before := fighters[1 - slot].energy
		rules.enter_frame()
		assert(fighters[1 - slot].energy == before)
		fighters[slot].health = 399
	var registry := SourceCallbackRegistry.new()
	var registration := registry.register(rules, "queue_frame", 4)
	var energy := fighters[0].energy
	registry.dispatch(4)
	rules.run_pending_frame()
	assert(fighters[0].energy == energy)
	registry.dispatch(5)
	assert(fighters[0].energy == energy)
	rules.run_pending_frame()
	assert(fighters[0].energy == energy + 0.2)
	rules.run_pending_frame()
	assert(fighters[0].energy == energy + 0.2)
	registry.unregister(registration)
	assert(registry.size() == 0)
	for fighter in fighters:
		fighter.queue_free()
	await process_frame
	print("SOURCE_HEALTH_RULES_SMOKE_OK")
	quit()
