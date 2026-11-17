extends "res://tests/move_case_reference.gd"

var visibility_rows: Array = []


func _observe(tick: int) -> void:
	super._observe(tick)
	for actor in [game.naruto, game.ichigo]:
		visibility_rows.append({"tick": tick, "slot": actor.player_slot, "visible": actor.visible})


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	await _run_case(args[0], args[1])
	FileAccess.open(args[1] + ".visibility.json", FileAccess.WRITE).store_string(JSON.stringify(visibility_rows))
	print("SASUKEXZ_VISIBILITY_REFERENCE_OK")
	quit()
