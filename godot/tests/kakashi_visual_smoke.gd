extends SceneTree

var failed := false


func check(condition: bool, message: String) -> void:
	if not condition:
		failed = true
		push_error(message)


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	root.transparent_bg = true
	var preview := TimelinePreview.new()
	preview.fighter_directory = "res://generated/fighters/kakashi"
	preview.autoplay = false
	preview.initial_action = "站立"
	root.add_child(preview)
	await process_frame
	check(preview._frames.size() == 1385, "Kakashi timeline frame count changed")
	check(preview._definitions.size() > 0, "Kakashi timeline definitions are missing")
	check(preview._assets.size() > 0, "Kakashi materialized assets are missing")
	var combo_range := preview.action_range("砍1")
	var super_range := preview.action_range("必杀")
	var ultimate_range := preview.action_range("超必杀")
	check(int(combo_range.get("start_frame", -1)) == 193 and int(combo_range.get("end_frame", -1)) == 218, "Kakashi combo range is not source-derived")
	check(int(super_range.get("start_frame", -1)) == 689 and int(super_range.get("end_frame", -1)) == 756, "Kakashi super range is not source-derived")
	check(int(ultimate_range.get("start_frame", -1)) == 863 and int(ultimate_range.get("end_frame", -1)) == 920, "Kakashi ultimate range is not source-derived")
	preview.play_action("砍1")
	check(preview.current_source_frame() == 193, "Kakashi action did not start at source frame 193")
	preview.play_source_frame(693)
	check(preview.current_source_frame() == 693, "Kakashi super source frame could not be selected")
	print("KAKASHI_VISUAL_SMOKE_FAILED" if failed else "KAKASHI_VISUAL_SMOKE_OK")
	quit(1 if failed else 0)
