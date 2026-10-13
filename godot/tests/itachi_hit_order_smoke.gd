extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/itachi"
	root.add_child(fighter)
	fighter.play_source_frame(534)
	# The native Flash enumeration probe visits zh32, zh31, then zh3;
	# the close-range up-U capture selects zh32 at fight tick 22.
	assert(fighter._ordered_attack_instances() == PackedStringArray([
		"zh32atm", "zh31atm", "zh3atm"]))
	fighter.queue_free()
	await process_frame
	print("ITACHI_HIT_ORDER_SMOKE_OK")
	quit()
