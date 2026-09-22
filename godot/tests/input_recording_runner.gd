extends SceneTree

# Developer entry point: -- record /absolute/output.json OR -- replay /absolute/input.json.
func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2 or args[0] not in ["record", "replay"]:
		push_error("Usage: -- record|replay /absolute/recording.json")
		quit(1)
		return
	var game = load("res://main.tscn").instantiate()
	root.add_child(game)
	current_scene = game
	var problem: String
	if args[0] == "record":
		problem = game.arm_input_recording(args[1])
	else:
		problem = game.start_input_playback(JSON.parse_string(FileAccess.get_file_as_string(args[1])))
	if not problem.is_empty():
		push_error(problem)
		quit(1)
