class_name SourceHitTest
extends RefCounted


static func intersects(receiver: Rect2, target: Rect2) -> bool:
	# Flash MovieClip.hitTest includes touching edges/corners. Empty clips
	# still have no receiver; see the retained native dash-edge probe.
	return receiver.has_area() and target.has_area() and receiver.intersects(target, true)
