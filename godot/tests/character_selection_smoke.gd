extends SceneTree

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var menu := CharacterSelection.new()
	root.add_child(menu)
	for mode in [1, 2, 3, 4]:
		menu.reset(mode)
		assert(menu.fighters[0] == "一护")
		assert(menu.enabled[1] == (mode == 3))
		if mode == 3:
			assert(menu.fighters[1] == "鸣人")
		menu.tick({"confirm": true}, {"confirm": true})
		assert(not menu.enabled[0])
		assert(menu.phase == 0)
		await create_timer(0.6).timeout
		if mode in [2, 4]:
			assert(menu.enabled[1])
			assert(menu.fighters[1] == "鸣人")
			menu.tick({"confirm": true}, {})
			await create_timer(0.6).timeout
		assert(menu.phase == 1)
		assert(menu.helpers[0] == "魂")
		menu.leave()
		await create_timer(0.6).timeout
		assert(not menu.visible)
	menu.queue_free()
	print("CHARACTER_SELECTION_SMOKE_OK")
	quit()
