extends SceneTree

func _initialize() -> void:
	_run.call_deferred()


func child_frame(clip: TimelinePreview) -> int:
	var placement: Dictionary = clip._frames[5].display_list[0]
	return clip._nested_frame(placement, 5, 30)


func _run() -> void:
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	game.set_physics_process(false)
	game._enter_current_fight(2)
	game.ichigo.ai_random_clock.cancel()
	for tick in 600:
		game._advance_fight()
		if not game.battle_intro.active:
			break
	var clip: TimelinePreview = game.black_mu
	game._on_ko_requested(2)
	assert(child_frame(clip) == 1)
	print("KO_BACKGROUND_FRAME 5,1")
	for tick in 10:
		game._advance_fight()
		game._sync_super_stage()
		game._sync_super_stage()
		if child_frame(clip) != tick + 2:
			push_error("KO background child must advance while its parent is stopped: tick %d, frame %d" % [tick + 1, child_frame(clip)])
			quit(1)
			return
		print("KO_BACKGROUND_FRAME 5,%d" % child_frame(clip))
	assert(game.ko_paused, "KOstart pauses fighters, not the root background clip")
	# Keep the isolated background selected past its final source stop frame.
	for tick in 25:
		clip.advance_display_timeline()
		assert(child_frame(clip) == mini(tick + 12, 30))
		print("KO_BACKGROUND_FRAME 5,%d" % child_frame(clip))
	assert(child_frame(clip) == 30)
	clip.play_source_frame(5)
	assert(child_frame(clip) == 30, "Repeated root synchronization must retain the child")
	clip.play_source_frame(1)
	clip.play_source_frame(5)
	assert(child_frame(clip) == 1, "A new placement must restart the KO background")
	game._goto_menu()
	game.queue_free()
	await process_frame
	print("KO_BACKGROUND_SMOKE_OK")
	quit()
