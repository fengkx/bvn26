extends "res://tests/sasukexz_render_settle_reference.gd"


func _observe(tick: int) -> void:
	super._observe(tick)
	if tick == bitmap_tick:
		# Diagnostic only: reconstruct derived CanvasItems without source advances.
		game.naruto.materialize_display()
		game.ichigo.materialize_display()
		game.current_world.materialize_display()
