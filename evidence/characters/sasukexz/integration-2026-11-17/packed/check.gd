extends SceneTree

func _initialize() -> void:
	assert(ProjectSettings.load_resource_pack(OS.get_cmdline_user_args()[0], true))
	var available: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/character_selection/available.json"))
	assert(available.fighters.size() == 35 and available.helpers.size() == 6)
	assert(available.fighters["佐助须佐"] == "sasukexz")
	for id in ["shouju", "ichigo", "minrenx", "sasukexz"]:
		assert(id in available.fighters.values())
		var fighter: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/fighters/%s/fighter.json" % id))
		assert(fighter.form_frame == 1)
	var intro: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/intro/intro.json"))
	assert(intro.fighters.has("sasukexz"))
	var portraits: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://generated/main/character_selection/portraits.json"))
	for texture in portraits["佐助须佐"].textures:
		assert(ResourceLoader.exists("res://generated/main/character_selection/" + texture))
	print("PACKED_SASUKEXZ_OK fighters=35 helpers=6 portrait_textures=true opening=true")
	quit()
