extends SceneTree

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	scene._enter_current_fight(3)
	var hud: HealthHud = scene.health_hud
	assert(hud.visible)
	assert(hud.size == Vector2(600, 400))
	scene.game_world.focus = "all"
	scene.naruto.position = Vector2(200, -400)
	scene.ichigo.position = Vector2(700, 100)
	scene._advance_world_and_markers([])
	var target := GameWorld.compute_target(scene.naruto.position, scene.ichigo.position, "all", scene.game_world.map_size_x)
	for index in 2:
		var marker: TimelinePreview = scene.player_markers[index]
		var actor: FighterRuntime = [scene.naruto, scene.ichigo][index]
		assert(marker.visible)
		var origin := marker.position + marker.wrapper_translation()
		assert(is_equal_approx(origin.x, SourceCoordinate.store(target.x + actor.position.x * target.scale)))
		assert(is_equal_approx(origin.y, [60.0, 390.0][index]))
	scene.naruto.position = Vector2(300, -25)
	scene.ichigo.position = Vector2(550, -25)
	scene._advance_world_and_markers([])
	assert(not scene.player_markers[0].visible and not scene.player_markers[1].visible)
	assert(not scene.fight_hud.visible)
	assert(hud.trail == [100.0, 100.0])
	scene.ichigo.health = 650
	scene.ichigo.hits = 2
	hud.refresh()
	assert(hud.trail[1] == 100.0)
	scene.ichigo.hits = 0
	hud.refresh()
	assert(hud.trail[1] == 98.0)
	scene.naruto.health = 190
	hud.refresh()
	assert(hud.low_health[0])
	scene.naruto.health = 0
	var previous := hud.trail.duplicate()
	hud.refresh()
	assert(hud.trail == previous)
	scene._enter_current_fight(3)
	assert(hud.trail == [100.0, 100.0])
	assert(not hud.low_health[0])
	scene.ichigo.health = 650
	scene.ichigo.hits = 2
	hud.refresh()
	await process_frame
	await process_frame
	if DisplayServer.get_name() != "headless":
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/bvn-hp-hud.png")
	scene._goto_menu()
	assert(not hud.visible)
	print("HEALTH_HUD_SMOKE_OK")
	quit()
