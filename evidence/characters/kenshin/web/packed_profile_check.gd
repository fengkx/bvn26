extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or not ProjectSettings.load_resource_pack(args[0], true):
		push_error("Expected an exported PCK")
		quit(1)
		return
	var profile = load("res://source_form_profile.gd")
	var sha := "648d781f59734e1b120b30c340685a74e223e5be49c186c31b796467db4f2e7f"
	for form in [2, 3]:
		var result: Dictionary = profile.prepare("res://generated/forms/kenshin-%d" % form, sha)
		if result.has("error"):
			push_error(str(result.error))
			quit(1)
			return
	if not profile.prepare("res://generated/forms/missing-kenshin-test", sha).has("error"):
		push_error("Missing resources must still fail preflight")
		quit(1)
		return
	print("KENSHIN_PACKED_PROFILES_OK 2/2; missing profile rejected")
	quit()
