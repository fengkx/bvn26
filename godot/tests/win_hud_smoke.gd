extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var hud := HealthHud.new()
	root.add_child(hud)
	assert(hud.win_placements(0).is_empty() and hud.win_placements(1).is_empty())
	for p1 in range(1, 4):
		for p2 in range(1, 4):
			hud.set_wins(p1, p2)
			assert(hud.win_placements(0).size() == p1 - 1)
			assert(hud.win_placements(1).size() == p2 - 1)
			for side in [0, 1]:
				for placement: Dictionary in hud.win_placements(side):
					assert(placement.character_id == 1784)
					assert(hud.textures[str(int(placement.character_id))] != null)
	# chushi refreshes health each round; it must not erase match wins.
	hud.reset()
	assert(hud.win_frames == PackedInt32Array([3, 3]))
	hud.queue_free()
	await process_frame
	print("WIN_HUD_SMOKE_OK")
	quit()
