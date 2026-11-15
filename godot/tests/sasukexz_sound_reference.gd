extends "res://tests/move_case_reference.gd"

var sound_rows: Array = []
var start_tick := 0


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	await _run_case(args[0], args[1])
	FileAccess.open(args[1] + ".sounds.json", FileAccess.WRITE).store_string(JSON.stringify(sound_rows, "  "))
	print("SASUKEXZ_SOUND_OBSERVER_OK ", sound_rows.size())
	quit(2 if failed else 0)


func _observe(tick: int) -> void:
	super._observe(tick)
	if tick == 0:
		start_tick = game.physics_tick
		game.naruto._sound_layer().child_entered_tree.connect(_sound_added)
	for entry in sound_rows:
		var player = instance_from_id(entry.instance_id)
		if is_instance_valid(player) and player.playing:
			entry["observed_playing"] = true


func _sound_added(player: Node) -> void:
	if player is AudioStreamPlayer:
		sound_rows.append({"tick": game.physics_tick - start_tick,
			"frame": game.naruto.current_source_frame(), "stream": player.stream.resource_path,
			"volume_db": player.volume_db, "instance_id": player.get_instance_id(),
			"observed_playing": false})
