extends "res://tests/sasukexz_blend_isolation_reference.gd"


func _save_groups() -> void:
	await super._save_groups()
	for child in game.naruto.get_children():
		if child.has_method("source_bounds") and child.has_node("Composite"):
			var composite: Sprite2D = child.get_node("Composite")
			# Diagnostic occlusion isolation, never a source depth correction.
			composite.z_as_relative = false
			composite.z_index = 300
