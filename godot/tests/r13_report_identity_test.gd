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
	# The pinned build omits p1cpu; its bootstrap explicitly assigns false.
	assert(not identity.configuration.has("p1cpu"))
	wrong = fixture.duplicate(true)
	wrong.session.p1cpu = true
	assert(Identity.runtime_error(wrong, identity) == "runtime_configuration_mismatch")
	var cpu_identity := identity.duplicate(true)
	cpu_identity.configuration.p1cpu = false
	assert(Identity.runtime_error(fixture, cpu_identity) == "")
	# Synthetic contract cases, not another qualified receipt/profile.
	cpu_identity.configuration.p1cpu = true
	assert(Identity.runtime_error(fixture, cpu_identity) == "runtime_configuration_mismatch")
	assert(Identity.runtime_error(wrong, cpu_identity) == "")
	cpu_identity.configuration.p1cpu = "false"
	assert(Identity.runtime_error(fixture, cpu_identity) == "invalid_p1_cpu_configuration")
	print("R13_IDENTITY_OK prior_cases_and_p1_cpu_default_explicit_mismatch_and_type_cases")
	quit()
