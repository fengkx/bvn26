extends SceneTree

var calls := 0


func callback() -> void:
	calls += 1


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var main = load("res://main.gd").new()
	main.naruto = FighterRuntime.new()
	main.ichigo = FighterRuntime.new()
	main.naruto_helper = HelperRuntime.new()
	main.naruto_helper._combat = JSON.parse_string(FileAccess.get_file_as_string("res://generated/helpers/jinye/combat.json"))
	main.ichigo_helper = HelperRuntime.new()
	main.ichigo_helper._combat = JSON.parse_string(FileAccess.get_file_as_string("res://generated/helpers/you/combat.json"))
	main.recorded_form_timers = true
	main.session.ai_level = 3
	main.session.codes["j"] = 86
	main.position.y = 17
	main._prepare_form_root_owner()
	var owner: SourceRootIntervals = main.source_root_intervals
	assert(owner.get_parent() == main and owner.recorded)
	assert(main.source_form_root_values.difficulty == 3)
	assert(main.source_form_root_values.root_y == 17)
	assert(main.source_form_root_values["key:j"] == 86)
	assert(main.source_form_root_values["helper_power:p1"].atm1pw == 60)
	assert(main.source_form_root_values["helper_power:p2"].atm3x == -3)
	assert(main.source_form_root_values.body_paths["/game/p1/mc"].get_ref() == main.naruto)
	assert(main._helper_source_power(null) == null)
	main._prepare_form_root_owner()
	assert(main.source_root_intervals == owner)
	var first := owner.assign_interval("feiint", callback, 1000)
	var second := owner.assign_interval("feiint2", callback, 1000)
	main._ko_clear_interval("feiint")
	assert(not owner.fire_recorded(first))
	assert(owner.fire_recorded(second) and calls == 1)
	main._apply_root_position("y", "+=", 5)
	assert(main.source_form_root_values.root_y == 22)
	main._stop_form_root_intervals()
	assert(owner.pending_count() == 0 and main.source_form_root_values.is_empty())
	main.naruto.free()
	main.ichigo.free()
	main.naruto_helper.free()
	main.ichigo_helper.free()
	# This fixture never enters Main._ready(), which normally parents this node.
	main.diagnostics.free()
	main.free()
	await process_frame
	print("FORM_ROOT_OWNER_SMOKE_OK")
	quit()
