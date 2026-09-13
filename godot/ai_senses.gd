class_name AiSenses
extends RefCounted

var fighter: TimelinePreview
var placement: Dictionary
var sensors: Dictionary = {}


func configure(owner_fighter: TimelinePreview, spec: Dictionary) -> void:
	fighter = owner_fighter
	placement = spec["sensing"]["placement"]
	sensors.clear()
	for sensor: Dictionary in spec["sensing"]["sensors"]:
		sensors[sensor["name"]] = sensor


func local_bounds(name: String) -> Rect2:
	if not sensors.has(name):
		return Rect2()
	# AImain is stopped on frame 2 by initCtrl. Its activation frame does not
	# follow the fighter's current source frame or nested autoplay clock.
	var bounds := fighter._placement_bounds(sensors[name], 2)
	var transform := fighter._wrapper_transform() * fighter._matrix_transform(
		placement.get("matrix", {}), 1.0
	)
	return fighter._transform_rect(transform, bounds)


func global_bounds(name: String) -> Rect2:
	if not sensors.has(name):
		return Rect2()
	return fighter.source_placement_global_bounds(sensors[name], 2, [placement])


func hit(name: String, opponent: TimelinePreview) -> Variant:
	if not sensors.has(name):
		# Preserve a missing instance separately from an ordinary miss. The
		# predicate's scalar compatibility layer handles the absent value.
		return null
	var target := opponent.instance_global_bounds("bdmn")
	if not target.has_area():
		return null
	return SourceHitTest.intersects(global_bounds(name), target)
