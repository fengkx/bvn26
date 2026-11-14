extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or not ProjectSettings.load_resource_pack(args[0], true):
		push_error("Expected an exported PCK")
		quit(1)
		return
	var profile = load("res://source_form_profile.gd")
	var sha := "ea72662bcb9c2a4c7ee9e9a81bb92c1beb1323f3982de86aa8e24a23286dc171"
	for form in [2]:
		var result: Dictionary = profile.prepare("res://generated/forms/weqal-%d" % form, sha)
		if result.has("error"):
			push_error(str(result.error))
			quit(1)
			return
	if not profile.prepare("res://generated/forms/missing-weqal-test", sha).has("error"):
		push_error("Missing resources must still fail preflight")
		quit(1)
		return
	print("WEQAL_PACKED_PROFILES_OK 1/1; missing profile rejected")
	quit()
