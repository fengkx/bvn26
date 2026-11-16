extends "res://tests/replay_display_smoke.gd"

const DisplayProjection = preload("res://authority_projection.gd")
const Wire = preload("res://authority_wire.gd")

func _run() -> void:
	# These replacement edges are retained in the corresponding form lifecycle tests.
	var cases := [
		{"fighter": "仙鸣", "edges": [1294]},
		{"fighter": "一护2", "edges": [886]},
		{"fighter": "剑心", "edges": [1148, 1503]},
		{"fighter": "小乌", "edges": [1148]},
	]
	var count := 0
	for case in cases:
		var fixture := Fixture.create(self, [case.fighter, "一护"], ["我爱罗", "魂"], "现世")
		var game: Node = fixture.game
		fixture.battle.close()
		assert(fixture.battle.configure(game, false).is_empty())
		game.recorded_form_timers = true
		game.source_root_intervals.recorded = true
		var capture := DisplayProjection.new()
		var presenter: Node = load("res://main.tscn").instantiate()
		presenter.prepare_presentation_only()
		root.add_child(presenter)
		var display := DisplayProjection.new()
		display.configure_presenter(presenter)
		for source_frame in case.edges:
			var driver: AiCpuDriver = game.player_body_driver._driver
			game.naruto.source_goto_frame(source_frame, true)
			driver.run_target_frames()
			assert(not game.naruto.source_body_available)
			driver.prepare_display_tick(count + 1)
			driver.advance_timeline()
			driver.run_target_frames()
			assert(game.naruto.source_body_available)
			var snapshot := capture.capture(game)
			if not capture.error.is_empty():
				push_error(capture.error)
				quit(1)
				return
			var wire := Wire.new()
			var encoded := wire.encode(snapshot)
			assert(not encoded.is_empty(), wire.error)
			assert(display.apply(wire.decode(encoded)).is_empty(), display.error)
			var guest: Node = display.nodes[capture._id(game.naruto)]
			var difference := State.first_difference(_visual(game.naruto), _visual(guest))
			if not difference.is_empty():
				push_error("%s: %s" % [case.fighter, difference])
				quit(1)
				return
			assert(presenter.physics_tick == 0)
			for owner in snapshot.owners:
				if owner.kind != "timeline" or owner.state.wrapper_clips.is_empty(): continue
				var invalid := snapshot.duplicate(true)
				for candidate in invalid.owners:
					if candidate.id == owner.id: candidate.state.wrapper_clips = []
				var retained := display.nodes.duplicate()
				assert(not display.apply(invalid).is_empty() and display.nodes == retained)
				break
			count += 1
		Fixture.dispose(game, fixture.battle)
		presenter.free()
		await process_frame
	print("AUTHORITY_FORM_PROJECTION_OK edges=%d guest_ticks=0" % count)
	quit()
