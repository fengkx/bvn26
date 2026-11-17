extends "res://tests/sasukexz_group_reference.gd"


func _save_groups() -> void:
	await super._save_groups()
	# Diagnose whether authored stage foreground owns the observed occlusion.
	game.current_world.set_hidden_instances(PackedStringArray(["fgmc"]))
