class_name ScriptedTimelinePreview
extends TimelinePreview

var scheduler := KoTimeline.new()


func _ready() -> void:
	super._ready()
	scheduler.configure(_timeline, _read_json(fighter_directory.path_join("controller.json")),
		load(fighter_directory.path_join("controller.gd")), _unsupported_service)
	play_source_frame(initial_frame)


func _unsupported_service(operation: String, _args: Array) -> Variant:
	assert(false, "Display-only timeline requested an uncompiled service: " + operation)
	return null


func play_source_frame(frame: int) -> void:
	if not scheduler.root_clip.is_empty() and int(scheduler.root_clip.frame) != frame:
		scheduler._goto(scheduler.root_clip, frame, false)
		scheduler.run_frame_actions()
	super.play_source_frame(frame)


func advance_display_timeline() -> void:
	# A stopped parent retains independently playing children, including during KO pause.
	scheduler.advance()
	super.play_source_frame(int(scheduler.root_clip.frame))


func _nested_frame(placement: Dictionary, timeline_frame: int, frame_count: int, clip_age: int = 0) -> int:
	if scheduler.root_clip.is_empty():
		return super._nested_frame(placement, timeline_frame, frame_count, clip_age)
	var matches: Array = []
	for clip: Dictionary in scheduler._ordered(scheduler.root_clip):
		if not clip.placement.is_empty() and is_same(clip.placement, placement):
			matches.append(clip)
	assert(matches.size() == 1, "Display placement must identify one live scheduled clip")
	return int(matches[0].frame)
