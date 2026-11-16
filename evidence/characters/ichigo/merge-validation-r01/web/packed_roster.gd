extends SceneTree

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	assert(args.size() == 2)
	assert(ProjectSettings.load_resource_pack(args[0], true))
	var expected := int(args[1])
	var available: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/character_selection/available.json"))
	assert(available.fighters.size() == expected)
	for id in ["shouju", "ichigo", "minrenx"]:
		if id == "minrenx" and expected == 33:
			continue
		assert(id in available.fighters.values())
		var fighter: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/%s/fighter.json" % id))
		assert(fighter.form_frame == 1)
	var profile = load("res://source_form_profile.gd")
	for id in ["ichigo", "minrenx"]:
		if id == "minrenx" and expected == 33:
			continue
		var fighter: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/%s/fighter.json" % id))
		var result: Dictionary = profile.prepare("res://generated/forms/%s-2" % id, fighter.source.swf_sha256)
		assert(not result.has("error"), str(result))
		assert(profile.prepare("res://generated/forms/missing-merge-test", fighter.source.swf_sha256).has("error"))
	print("PACKED_ROSTER_OK fighters=%d required_forms_loaded missing_profile_rejected" % expected)
	quit()
