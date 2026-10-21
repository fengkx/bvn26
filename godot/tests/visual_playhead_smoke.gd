extends SceneTree

func _initialize() -> void:
	var definition := {"frame_count": 3, "display_list_frame_events": [[], [], [{"visual_controls": [{"op": "stop"}]}]]}
	var clip := VisualPlayhead.create(definition)
	for tick in 20:
		VisualPlayhead.advance(clip, definition)
	assert(clip.frame == 3 and not clip.playing and clip.age == 20)
	var jump := {"frame_count": 4, "frame_labels": {"end": 4}, "display_list_frame_events": [[], [{"visual_controls": [{"op": "goto", "label": "end"}, {"op": "play"}]}], [], [{"visual_controls": [{"op": "stop"}]}]]}
	clip = VisualPlayhead.create(jump)
	VisualPlayhead.advance(clip, jump)
	assert(clip.frame == 4 and not clip.playing)
	for named in [false, true]:
		for paused in [false, true]:
			var preview := TimelinePreview.new()
			preview.independent_visual_clock = true
			preview._current_frame = 1
			preview._definitions = {7: {"type": "DefineSpriteTag", "frame_count": 3, "display_list_frames": [[], [], []], "display_list_frame_events": definition.display_list_frame_events}}
			var placement := {"depth": 2, "character_id": 7, "placed_frame": 1}
			if named: placement.name = "effect"
			for frame in 20:
				preview._frames[frame + 1] = {"display_list": [placement]}
			preview._sync_retained_visual_clips()
			for tick in 12:
				preview.advance_retained_visual_clips()
				if not paused: preview._current_frame += 1
				preview._sync_retained_visual_clips()
				assert(preview._nested_frame(placement, preview._current_frame, 3) == mini(tick + 2, 3))
			preview._frames[preview._current_frame].display_list = []
			preview._sync_retained_visual_clips()
			assert(preview._retained_visual_clips.is_empty())
			preview._frames[preview._current_frame].display_list = [placement]
			preview._sync_retained_visual_clips()
			assert(preview._nested_frame(placement, preview._current_frame, 3) == 1)
			preview.free()
	_shared_definition_instances()
	print("VISUAL_PLAYHEAD_OK named anonymous whiff hit_pause goto stop replacement")
	quit()


func _shared_definition_instances() -> void:
	# Two placements of one symbol share definition dictionaries, not playheads.
	# This reproduces staggered projectile children (e.g. the native air-U case).
	var preview := TimelinePreview.new()
	preview.independent_visual_clock = true
	preview._current_frame = 1
	var child := {"depth": 1, "character_id": 8, "placed_frame": 1}
	preview._definitions = {
		7: {"type": "DefineSpriteTag", "frame_count": 1, "display_list_frames": [[child]]},
		8: {"type": "DefineSpriteTag", "frame_count": 3, "display_list_frames": [
			[{"depth": 1, "character_id": 9}], [{"depth": 1, "character_id": 10}], [{"depth": 1, "character_id": 11}]],
			"display_list_frame_events": [[], [], [{"visual_controls": [{"op": "stop"}]}]]}}
	for index in 3:
		preview._definitions[9 + index] = {"type": "DefineShape3Tag", "shape_bounds_twips": {"Xmin": 0, "Ymin": 0, "Xmax": (index + 1) * 100, "Ymax": 100}}
	var first := {"depth": 2, "character_id": 7, "placed_frame": 1, "name": "first"}
	var second := {"depth": 3, "character_id": 7, "placed_frame": 2, "name": "second"}
	preview._frames = {1: {"display_list": [first]}}
	preview._sync_retained_visual_clips()
	preview.advance_retained_visual_clips()
	preview.advance_retained_visual_clips()
	preview._frames[1].display_list = [first, second]
	preview._sync_retained_visual_clips()
	assert(preview.instance_global_bounds("first").size.x == 15.0)
	assert(preview.instance_global_bounds("second").size.x == 5.0)
	preview.free()
