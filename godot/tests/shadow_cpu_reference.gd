extends "res://tests/dash_reference.gd"

var shadow_recorder = preload("res://tests/shadow_recorder.gd").new()

func _observe(tick: int) -> void:
	shadow_recorder.tick = tick
	if tick == 0:
		shadow_recorder.attach(game.game_world)
	super._observe(tick)
	if tick == 240:
		shadow_recorder.compare("res://../evidence/visual-audio/shadow/cpu/original-rows.json", "/tmp/bvn-shadow-cpu-rows.json")
