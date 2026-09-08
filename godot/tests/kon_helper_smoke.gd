extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.set_physics_process(false)
	scene._enter_current_fight(3)
	var kon: HelperRuntime = scene.ichigo_helper
	assert(kon.has_visual_timeline())
	assert(not kon.visible)
	assert(scene.ichigo_energy.helper_id == "魂")
	scene.naruto.energy = 300
	scene.ichigo.energy = 100
	scene.ichigo.enter_frame({"summon": true})
	assert(scene.ichigo.action == "招换")
	for tick in 30:
		scene._advance_fight()
		if kon.attacking:
			break
	assert(kon.attacking and kon.visible and kon.visual_child_count() > 0)
	assert(kon.current_source_frame() == 2)
	assert(scene.ichigo.energy == 0)
	assert(kon.owner_fighter == scene.ichigo and kon.facing == -1)
	var drains: Array[int] = []
	var last_energy: float = scene.naruto.energy
	for tick in 110:
		scene._advance_fight()
		var frame := kon.current_source_frame()
		if frame == 15:
			assert(kon.bs == 1 and kon.timeline_playing)
			assert(scene.super_runtime.zhanting)
			assert(not scene.naruto.timeline_playing)
			assert(scene.ichigo.bs == 1 and scene.ichigo.timeline_playing)
			assert(scene.super_runtime.last_xg == "XG_fzbs")
		if frame == 30:
			assert(not scene.super_runtime.zhanting)
			assert(scene.naruto.timeline_playing)
		if frame == 44:
			assert(kon._instance_local_offsets.is_empty(), "Kon has no Gaara aim load hook")
		if scene.naruto.energy != last_energy:
			drains.append(frame)
			assert(scene.naruto.energy == last_energy - 20)
			last_energy = scene.naruto.energy
		if frame == 72:
			kon.enter_frame()
			assert(scene.naruto.energy == last_energy, "A frame DoAction runs once while stopped")
		for child in scene.game_world.get_children():
			if child is HitEffectRuntime:
				child.auto_advance = false
				child.advance_effect()
		if frame == 80 and DisplayServer.get_name() != "headless":
			await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png("/tmp/bvn-kon-helper.png")
		if frame == 102:
			assert(kon.attacking, "fzccXg does not hide before the root wraps")
		if not kon.attacking:
			break
	assert(scene.ichigo.action == "站立" and scene.ichigo.bs == 0)
	scene.ichigo.enter_frame({"attack": true})
	assert(scene.ichigo.action == "砍1")
	assert(drains == [72, 75, 78, 81, 85, 89])
	assert(scene.naruto.energy == 180)
	assert(kon.current_source_frame() == 1 and not kon.visible and kon.bs == 0)
	# Both directions use the original local timeline geometry, including frame 44.
	for direction in [1, -1]:
		scene.naruto.start_action("站立")
		kon.activate({"x": 300, "y": -25, "facing": direction}, scene.ichigo)
		kon.play_source_frame(37)
		kon.enter_frame()
		assert(kon.instance_global_bounds("atm1").has_area())
		var box := kon.instance_global_bounds("atm1")
		var body: Rect2 = scene.naruto.instance_global_bounds("bdmn")
		scene.naruto.position += (box.get_center() - body.get_center()) / scene.game_world.scale
		var attack := kon.attack_contact(scene.naruto)
		assert(not attack.is_empty() and int(attack["damage"]) == 10)
		kon.apply_attack_contact(attack, scene.naruto)
		assert(kon.attack_contact(scene.naruto).is_empty())
		kon.play_source_frame(44)
		kon.enter_frame()
		assert(kon._instance_local_offsets.is_empty())
		kon.play_source_frame(65)
		assert(not kon.instance_global_bounds("atm1").has_area())
		kon.deactivate()
	print("KON_HELPER_SMOKE_OK")
	scene.queue_free()
	await process_frame
	quit()
