extends SceneTree

var game
var summon_slot := ""
var graphical := false


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	graphical = DisplayServer.get_name() != "headless"
	root.size = Vector2i(1038, 692)
	var surface := preload("res://render_surface.tscn").instantiate() as RenderSurface
	root.add_child(surface)
	surface._ios_web = true
	surface.web_raster_pixel_budget = RenderSurface.IOS_WEB_RASTER_PIXEL_BUDGET
	surface.source_viewport.set_meta("clip_offscreen_caches", true)
	surface.apply_quality("HIGH")
	game = surface.game
	game.set_physics_process(false)
	# The probe advances simulation ticks explicitly, independent of browser draw speed.
	game.ko_recorded_timers = true
	game.source_random.use_seed(2607)
	game.diagnostic_input_provider = func(slot: String, _tick: int) -> Dictionary:
		return {"summon": slot == summon_slot}
	game.arcade.stage = 6
	game.arcade.player = "一护万解"
	game.arcade.helper = "松本"
	await game._start_arcade_stage()
	await _finish_intro()
	# Run the next round through the real KO controller, with no summon inputs.
	game.ichigo.receive_attack({"damage": 2000, "horizontal_impulse": 0, "vertical_impulse": 0,
		"hitstun_ms": 100, "impact_strength": 1, "reaction_label": "被打"}, 1)
	for tick in 450:
		game._advance_fight()
		if game.ko_nextfight_timer != null:
			break
		if tick % 8 == 0:
			await process_frame
	assert(game.ko_nextfight_timer != null)
	game.ko_nextfight_timer.timeout.emit()
	await _finish_intro()
	assert(game.ko_state["_root.rounds"] == 2 and game.ichigo.health == game.session.maxhp)
	print("ROUND_WITHOUT_SUMMON_OK ", game.selected_stage)

	var roster: Dictionary = game.character_selection.available.helpers
	for label: String in roster:
		game._goto_menu()
		game._replace_selected_actors(["一护万解", "日番谷万解"], [label, label])
		game._enter_current_fight(3)
		await _finish_intro()
		await _summon("p1", label, 110.0)
		await _summon("p2", label, 420.0)
	game._goto_menu()
	for player in surface.find_children("*", "AudioStreamPlayer", true, false):
		player.stop()
		player.stream = null
	surface.queue_free()
	await process_frame
	await create_timer(0.2).timeout
	print("HELPER_ROSTER_RENDER_OK helpers=", roster.size(), " summons=", 2 * roster.size())
	quit()


func _finish_intro() -> void:
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			return
		if tick % 8 == 0:
			await process_frame
	assert(false, "Battle intro did not finish")


func _summon(slot: String, label: String, distance: float) -> void:
	var caster: FighterRuntime = game.naruto if slot == "p1" else game.ichigo
	var helper: HelperRuntime = game.naruto_helper if slot == "p1" else game.ichigo_helper
	assert(helper.helper_id == label)
	game.naruto.source_x = 220.0
	game.ichigo.source_x = 220.0 + distance
	for actor: FighterRuntime in [game.naruto, game.ichigo]:
		actor.sync_body_collision_position()
		actor.health = game.session.maxhp
	caster.energy = 300.0
	summon_slot = slot
	for tick in 120:
		game._advance_fight()
		if helper.attacking:
			break
		await process_frame
	summon_slot = ""
	assert(helper.attacking, "Summon failed: %s %s" % [label, slot])
	var peak_pixels := 0
	var peak_video := 0
	var peak_frame := 0
	var ticks := 0
	while helper.attacking and ticks < 360:
		var pixels := 0
		for target: SubViewport in helper.find_children("*", "SubViewport", true, false):
			pixels += target.size.x * target.size.y
			if helper.helper_directory.get_file() in ["soifong", "shishio"]:
				# These two unfiltered effects used to extend far beyond the stage.
				assert(target.size.x <= 602 and target.size.y <= 402)
		if pixels > peak_pixels:
			peak_pixels = pixels
			peak_frame = helper.current_source_frame()
		await process_frame
		if graphical:
			await RenderingServer.frame_post_draw
		peak_video = maxi(peak_video, int(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)))
		game._advance_fight()
		ticks += 1
	assert(not helper.attacking and not helper.visible and helper.current_source_frame() == 1)
	for tick in 45:
		game._advance_fight()
		if tick % 4 == 0:
			await process_frame
	await process_frame
	assert(helper.find_children("*", "SubViewport", true, false).is_empty())
	print("HELPER_RENDER ", JSON.stringify({"id": helper.helper_directory.get_file(), "slot": slot,
		"ticks": ticks, "peakPixels": peak_pixels, "peakFrame": peak_frame, "peakVideoBytes": peak_video}))
