class_name KoClip
extends TimelinePreview

var scheduler: KoTimeline


func _ready() -> void:
	assert(scheduler != null, "KO rendering requires a source timeline scheduler")
	fighter_directory = "res://generated/main/ko"
	autoplay = false
	super._ready()
	var metadata := _read_json(fighter_directory.path_join("ko.json"))
	transform = super._placement_transform(metadata.placement)
	z_index = int(metadata.placement.depth)
	refresh_from_scheduler()


func refresh_from_scheduler() -> void:
	play_source_frame(int(scheduler.root_clip.frame))


func _live_clip(placement: Dictionary) -> Dictionary:
	if scheduler == null:
		return {}
	var matches: Array[Dictionary] = []
	for clip: Dictionary in scheduler._ordered(scheduler.root_clip):
		if clip.placement.is_empty():
			continue
		if clip.symbol == int(placement.get("character_id", -1)) and int(clip.placement.depth) == int(placement.depth) and int(clip.placement.placed_frame) == int(placement.get("placed_frame", -1)):
			matches.append(clip)
	# The audited KO graph has one live occurrence of each sprite. Repeated
	# ambiguous occurrences require a parent path, not an arbitrary match.
	assert(matches.size() <= 1, "Ambiguous KO render placement")
	return matches[0] if not matches.is_empty() else {}


func _nested_frame(placement: Dictionary, _timeline_frame: int, _frame_count: int, _clip_age: int = 0) -> int:
	var clip := _live_clip(placement)
	assert(not clip.is_empty(), "KO child missing from source scheduler")
	return int(clip.frame)


func _placement_transform(placement: Dictionary) -> Transform2D:
	var result := super._placement_transform(placement)
	var clip := _live_clip(placement)
	if not clip.is_empty() and clip.x_override != null:
		result.origin.x = float(clip.x_override)
	return result
