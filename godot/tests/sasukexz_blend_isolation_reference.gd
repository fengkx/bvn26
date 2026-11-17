extends "res://tests/sasukexz_group_reference.gd"


func _save_groups() -> void:
	await super._save_groups()
	var details := []
	for child in game.naruto.get_children():
		if child.has_method("source_bounds") and child.has_node("Composite"):
			var composite: Sprite2D = child.get_node("Composite")
			var material: ShaderMaterial = composite.material
			details.append({"visible": composite.is_visible_in_tree(),
				"modulate": str(composite.modulate), "transform": str(composite.global_transform),
				"opacity": material.get_shader_parameter("group_opacity"),
				"blend_opacity": material.get_shader_parameter("blend_opacity"),
				"blend_mode": material.get_shader_parameter("flash_blend_mode")})
			# Isolate final composition only; this is not a product correction.
			composite.material = null
	FileAccess.open(bitmap_directory.path_join("isolation.json"), FileAccess.WRITE).store_string(JSON.stringify(details, "  "))
