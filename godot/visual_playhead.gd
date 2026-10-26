class_name VisualPlayhead
extends RefCounted

# Visual-only controls are compiled from self-contained SWF action blocks.
# Gameplay-owned named clips retain their authoritative source event driver.
static func enter_frame(clock: Dictionary, definition: Dictionary, on_frame: Callable = Callable()) -> void:
	var events: Array = definition.get("display_list_frame_events", [])
	var visited := {}
	while not visited.has(clock.frame):
		visited[clock.frame] = true
		var before := int(clock.frame)
		if on_frame.is_valid():
			on_frame.call(before)
		if before < 1 or before > events.size():
			return
		for event: Dictionary in events[before - 1]:
			for command: Dictionary in event.get("visual_controls", []):
				match str(command.op):
					"stop": clock.playing = false
					"play": clock.playing = true
					"goto":
						var target := int(command.get("frame", definition.get("frame_labels", {}).get(command.get("label", ""), before)))
						clock.frame = clampi(target, 1, int(definition.get("frame_count", 1)))
		if int(clock.frame) == before:
			return


static func create(definition: Dictionary, on_frame: Callable = Callable()) -> Dictionary:
	var clock := {"frame": 1, "playing": true, "age": 0, "children": {}}
	enter_frame(clock, definition, on_frame)
	return clock


static func advance(clock: Dictionary, definition: Dictionary, on_frame: Callable = Callable()) -> void:
	clock.age += 1
	if clock.playing:
		clock.frame = posmod(int(clock.frame), maxi(1, int(definition.get("frame_count", 1)))) + 1
		enter_frame(clock, definition, on_frame)
