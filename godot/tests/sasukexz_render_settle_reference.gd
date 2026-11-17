extends "res://tests/sasukexz_visual_phases.gd"


func _run() -> void:
	# Keep gameplay disabled while testing derived viewport composition latency.
	bitmap_settle_frames = 3
	await super._run()
