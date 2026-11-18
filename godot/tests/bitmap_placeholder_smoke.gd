extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Inputs = preload("res://rollback_test_session.gd")

var failed := false


func _initialize() -> void:
	_run.call_deferred()


func check(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)


func _run() -> void:
	var preview := TimelinePreview.new()
	preview.fighter_directory = "res://generated/fighters/yin"
	preview.autoplay = false
	preview.play_timeline_sounds = false
	root.add_child(preview)
	for child in preview.get_children():
		child.free()
	# A real texture with an explicit unused fill must not use the legacy fallback.
	var definition: Dictionary = preview._definitions[180].duplicate(true)
	definition.bitmap_clip_polygons = [[], [], []]
	preview._definitions[-2] = definition
	preview._render_placement({"character_id": -2}, Transform2D.IDENTITY, 1.0, 0, 1)
	check(preview.get_child_count() == 0, "Explicit empty masks drew a bitmap")
	var texture: Texture2D = load("res://generated/fighters/yin/%s" % preview._assets[int(definition.bitmap_fills[1].bitmap_id)])
	var size := texture.get_size()
	var rectangle := [[[0, 0], [size.x, 0], [size.x, size.y], [0, size.y]]]
	check(preview._mask_is_full_bitmap(rectangle, Transform2D.IDENTITY, texture), "Full bitmap rectangle lost Sprite2D path")
	var transformed := []
	var mirrored := Transform2D(Vector2(0, 2), Vector2(3, 0), Vector2(7.25, -4.5))
	for point: Array in rectangle[0]:
		var vertex := mirrored * Vector2(point[0], point[1])
		transformed.append([vertex.x, vertex.y])
	check(preview._mask_is_full_bitmap([transformed], mirrored, texture), "Transformed full rectangle lost Sprite2D path")
	check(not preview._mask_is_full_bitmap([[rectangle[0][0], rectangle[0][2], rectangle[0][1], rectangle[0][3]]], Transform2D.IDENTITY, texture), "Crossing contour used full bitmap")
	rectangle[0][1][0] -= 0.25
	check(not preview._mask_is_full_bitmap(rectangle, Transform2D.IDENTITY, texture), "Partial clip incorrectly used full bitmap")
	for shape_id in [180, 182, 224, 226]:
		definition = preview._definitions[shape_id]
		check(definition.bitmap_clip_polygons[0].is_empty(), "Placeholder lost its fill index")
		preview._render_placement({"character_id": shape_id}, Transform2D.IDENTITY, 1.0, 0, 1)
		check(preview.get_child_count() == definition.bitmap_fills.size() - 1, "Source fill count changed")
		# Every blade extension must remain clipped to the source contour.
		for index in range(1, preview.get_child_count()):
			var child := preview.get_child(index)
			check(child is Polygon2D, "Blade segment rendered as a full bitmap")
		for child in preview.get_children():
			child.free()
	# The same SWF sampling flag governs both full sprites and clipped polygons.
	for style in [0x40, 0x41, 0x42, 0x43]:
		var shape: Dictionary = preview._definitions[180].duplicate(true)
		for fill: Dictionary in shape.bitmap_fills:
			fill.fill_style_type = style
		preview._definitions[-2] = shape
		preview._render_placement({"character_id": -2}, Transform2D.IDENTITY, 1.0, 0, 1)
		var expected := CanvasItem.TEXTURE_FILTER_LINEAR if style < 0x42 else CanvasItem.TEXTURE_FILTER_NEAREST
		for leaf in preview.get_children():
			check(leaf.texture_filter == expected, "Wrong sampling for SWF bitmap fill %d" % style)
			leaf.free()
	preview.free()
	_check_corpus()
	for up in [false, true]:
		await _check_move(up)
	print("BITMAP_PLACEHOLDER_SMOKE_%s" % ("FAILED" if failed else "OK"))
	quit(1 if failed else 0)


func _check_corpus() -> void:
	var shapes := 0
	for folder in DirAccess.get_directories_at("res://generated/fighters"):
		var preview := TimelinePreview.new()
		preview.fighter_directory = "res://generated/fighters/" + folder
		preview.autoplay = false
		preview.play_timeline_sounds = false
		root.add_child(preview)
		for child in preview.get_children():
			child.free()
		for shape_id in preview._definitions:
			var definition: Dictionary = preview._definitions[shape_id]
			if not definition.has("bitmap_clip_polygons"):
				continue
			var masks: Array = definition.bitmap_clip_polygons
			check(masks.size() == definition.bitmap_fills.size(), "Mask/fill alignment lost in " + folder)
			var expected := 0
			for index in masks.size():
				if preview._assets.has(int(definition.bitmap_fills[index].bitmap_id)):
					expected += masks[index].size()
			preview._render_placement({"character_id": shape_id}, Transform2D.IDENTITY, 1.0, 0, 1)
			check(preview.get_child_count() == expected, "Empty or missing fill rendered in %s shape %s" % [folder, shape_id])
			for child in preview.get_children():
				child.free()
			shapes += 1
		preview.free()
	print("BITMAP_MASK_CORPUS shapes=", shapes)


func _check_move(up: bool) -> void:
	var fixture := Fixture.create(self, ["银", "一护"], ["我爱罗", "魂"], "现世")
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	if "--legacy-masks" in OS.get_cmdline_user_args():
		for shape_id in [180, 182, 224, 226]:
			game.naruto._definitions[shape_id].erase("bitmap_clip_polygons")
	var attack_start := -1
	var seen := {}
	var capture := "--capture" in OS.get_cmdline_user_args()
	for frame in range(1, 650):
		if not game.battle_intro.active and attack_start < 0:
			attack_start = frame + 5
			game.naruto.position.x = 200
			game.ichigo.position.x = 700
		var players := {"p1": {}, "p2": {}}
		for slot in players:
			for button in Inputs.BUTTONS:
				players[slot][button] = false
		players.p1.ranged = attack_start > 0 and frame >= attack_start and frame < attack_start + 3
		players.p1.up = up and players.p1.ranged
		var callbacks := []
		if game.battle_intro.polling and frame % 15 == 0:
			callbacks.append({"kind": "intro_poll", "phase": "after_actor_advance", "sequence": frame, "time_ms": frame * 33})
		check(battle.set_frame_events(frame, frame * 33, false, callbacks).is_empty(), "Frame event failed")
		check(battle.advance(frame, players).is_empty(), "Battle advance failed")
		var source_frame: int = game.naruto.current_source_frame()
		var first := 541 if up else 443
		var last := 548 if up else 454
		if source_frame >= first and source_frame <= last:
			seen[source_frame] = true
			check(game.find_children("*", "ShadowSnapshot", true, false).is_empty(), "Gin blade unexpectedly spawned an afterimage")
			if capture and source_frame == (545 if up else 450):
				await process_frame
				await RenderingServer.frame_post_draw
				root.get_texture().get_image().save_png("/tmp/bitmap-placeholder-mask/gin-%s%s.png" % ["up-u" if up else "u", "-before" if "--legacy-masks" in OS.get_cmdline_user_args() else ""])
		if attack_start > 0 and frame >= attack_start + 150:
			break
		if frame % 60 == 0:
			await process_frame
	check(seen.size() == (8 if up else 12), "Input did not traverse every affected source frame: %s" % [seen.keys()])
	print("GIN_MASK_INPUT up=", up, " source_frames=", seen.keys())
	Fixture.dispose(game, battle)
	await process_frame
