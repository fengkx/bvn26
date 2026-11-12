extends "res://tests/replay_display_smoke.gd"

const DisplayProjection = preload("res://authority_projection.gd")
const Wire = preload("res://authority_wire.gd")

func _run() -> void:
	var fixture := Fixture.create(self, ["鸣人", "一护"], ["我爱罗", "魂"], "现世")
	fixture.battle.close()
	assert(fixture.battle.configure(fixture.game, false).is_empty())
	var capture := DisplayProjection.new()
	fixture.game.set_meta("authority_projector", capture)
	var presenter: Node = load("res://main.tscn").instantiate()
	presenter.prepare_presentation_only()
	root.add_child(presenter)
	assert(presenter.get_child_count() == 0 and not presenter.is_physics_processing())
	var display := DisplayProjection.new()
	display.configure_presenter(presenter)
	var wire := Wire.new()
	var max_bytes := 0
	for frame in range(1, 331):
		var events := _frame_events(fixture.game, frame)
		assert(fixture.battle.set_frame_events(frame, events[0], events[1], events[2]).is_empty())
		assert(fixture.battle.advance(frame, _players(frame)).is_empty())
		if frame % 3 != 0: continue
		var snapshot := capture.capture(fixture.game)
		assert(capture.error.is_empty(), capture.error)
		var bytes := wire.encode(snapshot)
		assert(not bytes.is_empty(), wire.error)
		max_bytes = maxi(max_bytes, bytes.size())
		var decoded := wire.decode(bytes)
		var problem := display.apply(decoded)
		assert(problem.is_empty(), problem)
		for host_id in capture._ids:
			var id: int = capture._ids[host_id]
			if not display.nodes.has(id) or not is_instance_id_valid(host_id): continue
			var host_node: Node = instance_from_id(host_id)
			if not host_node is TimelinePreview: continue
			var difference := State.first_difference(_visual(host_node), _visual(display.nodes[id]))
			assert(difference.is_empty(), "%s frame=%d %s" % [host_node.name, frame, difference])
		assert(presenter.physics_tick == 0)
		await process_frame
	fixture.game.naruto.goto_ai_label("走", false)
	var shadow := ShadowSnapshot.new()
	fixture.game.game_world.add_child(shadow)
	shadow.capture(fixture.game.naruto, {"R": 30, "G": 10, "B": 0}, fixture.game.source_callbacks, 331)
	var shadow_state := capture.capture(fixture.game)
	assert(display.apply(wire.decode(wire.encode(shadow_state))).is_empty())
	var guest_shadow: ShadowSnapshot = display.nodes[capture._id(shadow)]
	assert(shadow.bitmap_size == guest_shadow.bitmap_size and shadow.bounds == guest_shadow.bounds)
	assert(State.first_difference(_visual(shadow.capture_viewport.get_child(0)), _visual(guest_shadow.capture_viewport.get_child(0))).is_empty())
	var malformed := shadow_state.duplicate(true)
	malformed.owners[0].transform = [NAN, 0, 0, 0, 0, 0]
	var retained := display.nodes.duplicate()
	assert(not display.apply(malformed).is_empty() and display.nodes == retained)
	shadow.dispose()
	print("AUTHORITY_PROJECTION_OK frames=330 dropped=220 max_bytes=%d guest_ticks=0" % max_bytes)
	Fixture.dispose(fixture.game, fixture.battle)
	presenter.free()
	await process_frame
	quit()
