extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or not ProjectSettings.load_resource_pack(args[0], true):
		push_error("Expected an exported PCK")
		quit(1)
		return
	var profile = load("res://source_form_profile.gd")
	var sha := "21bf68e942d417b0b39e8702ae388b8146a9c275510d83125d51a4f08dd9723f"
	for form in [2]:
		var result: Dictionary = profile.prepare("res://generated/forms/ichigo-%d" % form, sha)
		if result.has("error"):
			push_error(str(result.error))
			quit(1)
			return
	if not profile.prepare("res://generated/forms/missing-ichigo-test", sha).has("error"):
		push_error("Missing resources must still fail preflight")
		quit(1)
		return
	print("ICHIGO_PACKED_PROFILES_OK 1/1; missing profile rejected")
	quit()
