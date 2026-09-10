extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	await process_frame

	var available: Dictionary = scene.character_selection.available
	var portraits: Dictionary = scene.character_selection._portrait_spec
	var footer: Dictionary = scene.character_selection._footer_spec
	for name in ["佐助", "卡卡西", "恋次"]:
		assert(portraits.has(name), "Missing selectable fighter portrait: " + name)
		assert(footer.has(name), "Missing selectable fighter footer name: " + name)
		for texture: String in portraits[name].textures:
			assert(FileAccess.file_exists("res://generated/main/character_selection/" + texture))
	assert(footer.has("鼬"), "Missing selectable helper footer name: 鼬")
	assert(available.fighters == {
		"鸣人": "minren", "一护": "yihu", "日番谷": "rifagu",
		"佐助": "sasuke", "卡卡西": "kakashi", "恋次": "renji",
	})
	assert(available.helpers == {"我爱罗": "woailuo", "魂": "kon", "鼬": "you"})

	scene._goto_character_selection(3)
	scene._on_characters_confirmed(["佐助", "恋次"], ["鼬", "魂"])
	assert(scene.naruto.fighter_directory == "res://generated/fighters/sasuke")
	assert(scene.ichigo.fighter_directory == "res://generated/fighters/renji")
	assert(scene.naruto_helper.helper_id == "鼬")
	assert(scene.ichigo_helper.helper_id == "魂")
	scene._on_map_confirmed("现世")
	assert(not scene.session.p2cpu)
	assert(scene.player_body_driver != null and scene.opponent_driver != null)

	scene._goto_menu()
	scene._goto_character_selection(2)
	scene._on_characters_confirmed(["卡卡西", "恋次"], ["我爱罗", "鼬"])
	assert(scene.naruto.fighter_directory == "res://generated/fighters/kakashi")
	assert(scene.ichigo.fighter_directory == "res://generated/fighters/renji")
	assert(scene.naruto_helper.helper_id == "我爱罗")
	assert(scene.ichigo_helper.helper_id == "鼬")
	scene._on_map_confirmed("现世")
	assert(scene.session.p2cpu)
	assert(scene.player_body_driver != null and scene.opponent_driver != null)

	print("EXPANDED_SELECTION_SMOKE_OK")
	scene.queue_free()
	quit()
