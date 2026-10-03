class_name ComboHud
extends Control

# Source: main.swf DefineSprite_1833 + p1hits.pn=2 / p2hits.pn=1.
# Presentation only. Does not write fighter.hits or health.

var spec: Dictionary = {}
var _boards: Dictionary = {}


func set_presentation_enabled(enabled: bool) -> void:
	visible = enabled
	if enabled:
		remove_meta("suppress_display")
	else:
		set_meta("suppress_display", true)
	for board: Dictionary in _boards.values():
		var preview: TimelinePreview = board.preview
		if enabled:
			preview.remove_meta("suppress_display")
			preview.materialize_display()
		else:
			preview.set_meta("suppress_display", true)


func load_spec(path: String) -> void:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		spec = parsed.get("combo_hud", {})
	_ensure_boards()


func play(board_pn: int, hit_count: int) -> void:
	_ensure_boards()
	if not _boards.has(board_pn):
		return
	var board: Dictionary = _boards[board_pn]
	board["playing"] = true
	# Source: gotoAndPlay("连击") starts at DefineSprite_1833 label frame.
	board["frame"] = int(spec.get("play_frame", spec.get("show_number_frame", 11)))
	board["hits"] = hit_count
	_refresh(board_pn)


func tick() -> void:
	if spec.is_empty():
		return
	var reset_frame := int(spec.get("reset_frame", 50))
	for board_pn in _boards.keys():
		var board: Dictionary = _boards[board_pn]
		if not bool(board.get("playing", false)):
			continue
		board["frame"] = int(board["frame"]) + 1
		if int(board["frame"]) >= reset_frame:
			board["playing"] = false
			board["frame"] = int(spec.get("stop_frame", 1))
		_refresh(int(board_pn))


func showing(board_pn: int) -> bool:
	if not _boards.has(board_pn):
		return false
	var board: Dictionary = _boards[board_pn]
	if not bool(board.get("playing", false)):
		return false
	return int(board.get("frame", 0)) >= int(spec.get("show_number_frame", 11))


func displayed_hits(board_pn: int) -> int:
	if not showing(board_pn):
		return 0
	return int(_boards[board_pn].get("hits", 0))


func _ensure_boards() -> void:
	if spec.is_empty() or not _boards.is_empty():
		return
	_make_board(1, false)
	_make_board(2, true)


func _make_board(board_pn: int, _mirrored: bool) -> void:
	var preview := TimelinePreview.new()
	if has_meta("suppress_display"):
		preview.set_meta("suppress_display", true)
	preview.fighter_directory = "res://generated/main/combo"
	preview.autoplay = false
	preview.show_collision_shapes = false
	add_child(preview)
	var source_name := "p1hits" if board_pn == 1 else "p2hits"
	var placement: Dictionary = preview._timeline["boards"][source_name]
	preview.transform = preview._placement_transform(placement)
	_boards[board_pn] = {
		"preview": preview,
		"playing": false,
		"frame": int(spec.get("stop_frame", 1)),
		"hits": 0,
		"number": 0,
		"number_initialized": false,
	}


func _refresh(board_pn: int) -> void:
	var board: Dictionary = _boards[board_pn]
	var preview := board["preview"] as TimelinePreview
	var frame := int(board["frame"])
	# DefineSprite_1827 stops at 1 on placement; changeNum runs at frame 11.
	if frame == int(spec.get("stop_frame", 1)):
		board["number"] = 0
		board["number_initialized"] = false
	elif frame == int(spec.get("show_number_frame", 11)):
		board["number"] = maxi(0, int(board["hits"]))
		board["number_initialized"] = true
	var count := int(board["number"])
	preview.hidden_instance_names.clear()
	if bool(board["number_initialized"]):
		if count < 100:
			preview.hidden_instance_names.append("百")
		if count < 10:
			preview.hidden_instance_names.append("十")
	preview.set_instance_clip_frame("百", mini(count / 100 + 1, 10), false)
	preview.set_instance_clip_frame("十", (count / 10) % 10 + 1, false)
	preview.set_instance_clip_frame("个", count % 10 + 1, false)
	preview.play_source_frame(frame)
