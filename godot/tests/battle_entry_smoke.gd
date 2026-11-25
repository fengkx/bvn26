extends SceneTree


func _initialize() -> void:
	run.call_deferred()


func run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game._goto_character_selection(2)
	game.character_selection.confirmed.emit(["一护", "鸣人"], ["魂", "我爱罗"])
	game.map_selection.confirmed.emit("现世")
	var screen = game._pack_screen
	assert(is_instance_valid(screen))
	assert(screen.labels == ["一护", "鸣人"])
	assert(game.session.root_label != "游戏场景")
	var key := InputEventKey.new()
	key.keycode = game.session.flash_to_key(game.session.codes.j)
	key.pressed = true
	screen._input(key)
	assert(screen.frame < 27, "The skip key must be inactive during the entrance")
	while screen.frame < 28:
		await process_frame
	screen.loaded = false
	screen.frame = 171
	screen.meter_frame = 0
	screen._process(2.0)
	screen._input(key)
	assert(screen.frame == 172, "Slow downloads must hold the last matchup frame")
	screen.loaded = true
	screen._process(1.0 / float(screen.timeline.fps))
	assert(screen.frame == 172)
	screen.meter_frame = 9
	screen._input(key)
	assert(screen.frame == 173, "Skipping must play the closing shutter")
	while is_instance_valid(game._pack_screen):
		await process_frame
	assert(game.session.root_label == "游戏场景")
	print("BATTLE_ENTRY_CACHE_WAIT_AND_SKIP_OK")
	game.queue_free()
	await process_frame
	quit()
