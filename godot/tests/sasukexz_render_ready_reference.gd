extends "res://tests/sasukexz_visual_phases.gd"


func _run() -> void:
	# Diagnose renderer readiness with source clocks and gameplay frozen.
	bitmap_settle_frames = 120
	await super._run()
