extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	await process_frame

	# Test-only mappings exercise fixture loading without opening the menu roster.
	game.character_selection.available.fighters["樱"] = "sakura"
	game.character_selection.available.helpers["松本·井野"] = "jinye"
	game._replace_selected_actors(["樱", "一护"], ["松本·井野", "魂"])
	await process_frame

	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://../manifest.json"))
	for record in [
		{"helper": game.naruto_helper, "id": "松本", "path": "game/fighter/fz/jinye.swf"},
		{"helper": game.ichigo_helper, "id": "魂", "path": "game/fighter/fz/kon.swf"},
	]:
		var helper: HelperRuntime = record.helper
		var expected_hash := str(manifest.file_sha256[record.path])
		var combat_source: Dictionary = helper._combat.source
		var timeline_source: Dictionary = helper._timeline.source_swf
		assert(helper.helper_id == record.id)
		assert(str(combat_source.swf) == record.path)
		assert(str(combat_source.swf_sha256) == expected_hash)
		assert(str(timeline_source.path) == record.path)
		assert(str(timeline_source.sha256) == expected_hash)
		assert(FileAccess.get_sha256("res://../" + record.path) == expected_hash)
		print("HELPER_BINDING ", JSON.stringify({
			"helper_id": helper.helper_id,
			"directory": helper.helper_directory,
			"combat_source": combat_source.swf,
			"combat_sha256": combat_source.swf_sha256,
			"timeline_source": timeline_source.path,
			"timeline_sha256": timeline_source.sha256,
		}))

	# Exercise the reported lineup through the normal summon input. The authored
	# command and helper asset have different source names from the selection UI.
	game._replace_selected_actors(["日番谷", "一护"], ["松本", "魂"])
	game._load_selected_stage("楼顶")
	game._enter_current_fight(3)
	for tick in 700:
		game._advance_fight()
		if not game.battle_intro.active:
			break
		if tick % 10 == 0:
			await process_frame
	var activations: Array[Dictionary] = []
	game.diagnostics.event_recorded.connect(func(event: Dictionary) -> void:
		if event.type == "helper_lifecycle" and event.payload.ownerSlot == "p1":
			activations.append(event.payload))
	game.naruto.energy = 300.0
	game.session.touch_slots.o = true
	for tick in 15:
		game._advance_fight()
		if game.naruto_helper.attacking:
			break
	game.session.touch_slots.erase("o")
	assert(activations.size() == 1)
	var player: Dictionary = game._diagnostic_player(game.naruto, game.naruto_helper)
	assert(player.displayName == "日番谷·东狮郎")
	assert(player.helper.attacking and player.helper.id == "jinye")
	assert(player.helper.displayName == "山中井野" and player.helper.sourceId == "松本")
	assert(activations[0].helper == player.helper.displayName)
	assert(activations[0].sourceId == player.helper.sourceId)
	assert(activations[0].resourcePath == player.helper.resourcePath)

	game._goto_menu()
	for node in game.find_children("*", "", true, false):
		if node is AudioStreamPlayer or node is AudioStreamPlayer2D:
			node.stop()
			node.stream = null
	await process_frame
	game.queue_free()
	await process_frame
	await create_timer(0.2).timeout
	print("SAKURA_INO_HELPER_BINDING_SMOKE_OK")
	quit()
