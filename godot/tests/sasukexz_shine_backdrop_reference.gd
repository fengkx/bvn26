extends "res://tests/sasukexz_group_reference.gd"


func _observe(tick: int) -> void:
	super._observe(tick)
	if tick == bitmap_tick:
		var backdrop := BackBufferCopy.new()
		backdrop.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
		backdrop.show_behind_parent = true
		game.screen_flash.add_child(backdrop)
