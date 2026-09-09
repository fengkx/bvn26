extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _step(driver: Node, registry: SourceCallbackRegistry, tick: int, inputs: Dictionary) -> void:
	driver.begin_tick(tick, inputs)
	driver.advance_timeline()
	driver.prepare_callbacks()
	registry.dispatch(tick)
	driver.fighter.run_frame_actions()


func _run() -> void:
	var player := FighterRuntime.new()
	player.fighter_directory = "res://generated/fighters/minren"
	var opponent := FighterRuntime.new()
	opponent.fighter_directory = "res://generated/fighters/yihu"
	opponent.player_slot = "p2"
	root.add_child(player)
	root.add_child(opponent)
	player.opponent = opponent
	opponent.opponent = player
	for fighter: FighterRuntime in [player, opponent]:
		fighter.ai_source_state.apply_load()
		fighter.ai_source_state.apply_frame(1)
	player.position = Vector2(200, -25)
	opponent.position = Vector2(900, -25)
	var registry := SourceCallbackRegistry.new()
	var driver = preload("res://player_body_driver.gd").new()
	root.add_child(driver)
	driver.configure(player, "res://generated/fighters/minren/player_controller", {}, -25, 1000,
		func(_name: String, _args: Array) -> Variant: return null, registry)
	for tick in range(1, 7):
		_step(driver, registry, tick, {"right": true})
		assert(player.current_source_frame() == 10 and player.position.x == 200 + tick * 8)
		assert(player.facing == 1)
		assert(player.transform.x.x > 0 and player.transform.y.y > 0)
		assert(player.unnamed_sprite_local_frame(31) == tick, "Held movement must advance the retained run clip")
	# Both cached direction predicates are true: preserve both ordered moves/gotos.
	_step(driver, registry, 7, {"left": true, "right": true})
	assert(player.position.x == 248 and player.current_source_frame() == 10 and player.facing == 1)
	for tick in [8, 9]:
		_step(driver, registry, tick, {})
		assert(player.current_source_frame() == tick + 3)
	_step(driver, registry, 10, {})
	assert(player.current_source_frame() == 1)
	_step(driver, registry, 11, {"left": true})
	assert(player.position.x == 240 and player.facing == -1)
	assert(player.unnamed_sprite_local_frame(31) == 1, "Replaced run clip must restart")
	for tick in range(12, 44):
		var direction := -1 if tick < 28 else 1
		_step(driver, registry, tick, {"left": direction < 0, "right": direction > 0})
		assert(player.facing == direction)
		assert(signf(player.global_transform.x.x) == direction and player.global_transform.y.y > 0,
			"Rendered direction must follow held/reversed input")
		assert(player.unnamed_sprite_local_frame(31) == (tick - 11) % 14 + 1,
			"Run clip must loop and survive reversal without restarting")
	# The first goto removes the stand controller, so attack cannot override guard.
	_step(driver, registry, 44, {"down": true, "attack": true})
	assert(player.action == "防御")
	# Source placement load samples speed once, not on every projectile callback.
	driver.begin_tick(50, {})
	player.ai_source_state.values["speed"] = 8
	player.goto_ai_label("招1", true)
	player.play_source_frame(382)
	player._queue_source_frame(382)
	driver.prepare_callbacks()
	registry.dispatch(50)
	assert(player.instance_local_offset("zh1atm") == Vector2.ZERO)
	player.ai_source_state.values["speed"] = 1
	driver.begin_tick(51, {})
	driver.prepare_callbacks()
	registry.dispatch(51)
	assert(player.instance_local_offset("zh1atm") == Vector2(16, 0))
	driver.stop()
	assert(registry.size() == 0 and not player.ai_timeline_controlled)
	driver.queue_free()
	player.queue_free()
	opponent.queue_free()
	await process_frame
	print("PLAYER_CONTROLLER_SMOKE_OK")
	quit()
