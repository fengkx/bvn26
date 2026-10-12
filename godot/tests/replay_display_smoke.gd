extends "res://tests/rollback_delayed_input_profile.gd"


func _visual(node: Node) -> Array:
	var result := []
	for child in node.get_children():
		if child.is_queued_for_deletion() or child.name in ["SoundLayer", "RuntimeServices"]:
			continue
		var item := {"class": child.get_class()}
		if child is Node2D:
			item.transform = child.transform
			item.modulate = child.modulate
			item.z = child.z_index
		if child is Sprite2D:
			item.texture = _texture(child.texture)
			item.offset = child.offset
		if child is Polygon2D:
			item.texture = _texture(child.texture)
			item.polygon = child.polygon
			item.uv = child.uv
		if child is CanvasItem and child.material is ShaderMaterial:
			item.shader = child.material.shader.code
			item.uniforms = {}
			for uniform in child.material.shader.get_shader_uniform_list():
				item.uniforms[uniform.name] = child.material.get_shader_parameter(uniform.name)
		item.children = _visual(child)
		result.append(item)
	return result


func _texture(texture: Texture2D) -> Variant:
	if texture is AtlasTexture: return [_texture(texture.atlas), texture.region, texture.margin]
	return texture.resource_path if texture != null else ""


func _run() -> void:
	var fixtures := []
	for deferred in [false, true]:
		var container := Node.new()
		root.add_child(container)
		var field_roster := OS.get_cmdline_user_args().has("--field-roster")
		var fixture := Fixture.create(self, ["白哉", "小李"], ["松本", "我爱罗"], "温泉", container) if field_roster else Fixture.create(self, [], [], "", container)
		fixture.container = container
		fixture.battle.checkpoint.defer_replay_display = deferred
		var events: Array = []
		fixture.events = events
		fixture.game.diagnostics.event_recorded.connect(func(event: Dictionary) -> void:
			events.append({"type": event.type, "tick": event.get("fightTick", -1), "payload": event.payload}))
		fixtures.append(fixture)
	var compared := 0
	for start in range(1, 331, 6):
		for fixture in fixtures: fixture.battle.begin_replay()
		for frame in range(start, mini(start + 6, 331)):
			for fixture in fixtures:
				var events := _frame_events(fixture.game, frame)
				assert(fixture.battle.set_frame_events(frame, events[0], events[1], events[2]).is_empty())
				assert(fixture.battle.advance(frame, _players(frame)).is_empty())
			assert(State.first_difference(fixtures[0].battle.save_state(), fixtures[1].battle.save_state()).is_empty())
		for fixture in fixtures: fixture.battle.end_replay()
		for key in ["naruto", "ichigo", "current_world", "black_mu", "ts_face", "naruto_helper", "ichigo_helper"]:
			assert(State.first_difference(_visual(fixtures[0].game.get(key)), _visual(fixtures[1].game.get(key))).is_empty(), key)
			compared += 1
		assert(fixtures[1].battle.checkpoint._pending_displays.is_empty())
		await process_frame
	assert(fixtures[0].events.is_empty() and fixtures[1].events.is_empty(), "Replay must not record diagnostic events")
	# BitmapData consumers must see the current pose, before the final flush.
	for fixture in fixtures:
		fixture.battle.begin_replay()
		fixture.game.naruto.goto_ai_label("走", false)
		var shadow := ShadowSnapshot.new()
		fixture.game.game_world.add_child(shadow)
		shadow.capture(fixture.game.naruto, {}, fixture.game.source_callbacks, 331)
		fixture.shadow = shadow
	assert(State.first_difference(_visual(fixtures[0].shadow.capture_viewport.get_child(0)), _visual(fixtures[1].shadow.capture_viewport.get_child(0))).is_empty())
	for fixture in fixtures:
		fixture.shadow.dispose()
		fixture.battle.end_replay()
	var counters: Dictionary = fixtures[1].battle.checkpoint.profile
	assert(counters.display_deferred_count > counters.display_flush_count)
	print("REPLAY_DISPLAY_SMOKE_OK states=330 visual_comparisons=%d shadow_current_pose=true deferred=%d flushed=%d" % [compared, counters.display_deferred_count, counters.display_flush_count])
	for fixture in fixtures:
		Fixture.dispose(fixture.game, fixture.battle)
		fixture.container.free()
	await process_frame
	quit()
