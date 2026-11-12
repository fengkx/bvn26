extends SceneTree

const Identity = preload("res://tests/r13_report_identity.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var path := OS.get_cmdline_user_args()[0]
	var identity := Identity.qualify(path)
	assert(identity.error == "")
	assert(identity.body_boundaries == true)
	var fixture := {
		"naruto": {"fighter_directory": "res://generated/fighters/minren", "player_slot": "p1"},
		"ichigo": {"fighter_directory": "res://generated/fighters/yihu", "player_slot": "p2"},
		"selected_stage": "现世",
		"session": {"modo": 2, "ai_level": 5, "p2cpu": true, "p1cpu": false},
		"naruto_helper": {"helper_id": "我爱罗", "helper_directory": "res://generated/helpers/woailuo"},
		"ichigo_helper": {"helper_id": "魂", "helper_directory": "res://generated/helpers/kon"}}
	assert(Identity.runtime_error(fixture, identity) == "")
	var wrong := fixture.duplicate(true)
	wrong.ichigo.fighter_directory = "res://generated/fighters/byakuya"
	assert(Identity.runtime_error(wrong, identity) == "runtime_fighter_identity_mismatch")
	wrong = fixture.duplicate(true)
	wrong.naruto.player_slot = "p2"
	assert(Identity.runtime_error(wrong, identity) == "runtime_fighter_identity_mismatch")
	wrong = fixture.duplicate(true)
	wrong.session.ai_level = 4
	assert(Identity.runtime_error(wrong, identity) == "runtime_configuration_mismatch")
	wrong = fixture.duplicate(true)
	wrong.ichigo_helper.helper_id = "我爱罗"
	assert(Identity.runtime_error(wrong, identity) == "runtime_helper_identity_mismatch")
	var wrong_identity := identity.duplicate(true)
	wrong_identity.sources_sha256["game/fighter/yihu.swf"] = "incorrect"
	assert(Identity.runtime_error(fixture, wrong_identity) == "generated_source_identity_mismatch")
	wrong_identity = identity.duplicate(true)
	wrong_identity.sources_sha256["game/fighter/fz/kon.swf"] = "incorrect"
	assert(Identity.runtime_error(fixture, wrong_identity) == "generated_helper_identity_mismatch")
	print("R13_IDENTITY_OK positive_and_six_negative_cases")
	quit()
