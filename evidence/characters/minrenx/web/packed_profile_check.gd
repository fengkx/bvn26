extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or not ProjectSettings.load_resource_pack(args[0], true):
		push_error("Expected an exported PCK")
		quit(1)
		return
	var profile = load("res://source_form_profile.gd")
	var sha := "3ab1aa4fa7bf8301cc4ec480517ab8f23e29dc82867ee8bcc1741fee20637bde"
	for form in [2]:
		var result: Dictionary = profile.prepare("res://generated/forms/minrenx-%d" % form, sha)
		if result.has("error"):
			push_error(str(result.error))
			quit(1)
			return
	if not profile.prepare("res://generated/forms/missing-minrenx-test", sha).has("error"):
		push_error("Missing resources must still fail preflight")
		quit(1)
		return
	print("MINRENX_PACKED_PROFILES_OK 1/1; missing profile rejected")
	quit()
