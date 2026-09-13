extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var caster := FighterRuntime.new()
	caster.fighter_directory = "res://generated/fighters/minren"
	root.add_child(caster)
	await process_frame
	var state := {"canhit": true, "opponent_action": 0, "opponent_helper_action": null, "defran": 129}
	var predicates = load("res://generated/fighters/yihu/ai_controller/predicates.gd").new(state)
	for helper_name: String in ["woailuo", "kon"]:
		var helper := HelperRuntime.new()
		helper.helper_directory = "res://generated/helpers/" + helper_name
		root.add_child(helper)
		assert(helper.source_action == null)
		helper.activate({"x": 300, "y": 0, "facing": 1}, caster)
		assert(helper.source_action == null)
		state.opponent_helper_action = helper.source_action
		assert(not predicates.defence())
		# Root DoAction sets 动作=1 at woailuo 13 / kon 12.
		var action_frame := 13 if helper_name == "woailuo" else 12
		helper.play_source_frame(action_frame - 1)
		helper.enter_frame()
		assert(helper.source_action == null)
		helper.play_source_frame(action_frame)
		helper.enter_frame()
		assert(helper.source_action == 1)
		state.opponent_helper_action = helper.source_action
		state.defran = 129
		assert(predicates.defence())
		state.defran = 130
		assert(not predicates.defence())
		if helper_name == "kon":
			helper.play_source_frame(67)
			helper.enter_frame()
			assert(helper.source_action == 0)
		else:
			# Woailuo frame 85 only emits fzccXg, then its timeline returns to
			# frame 1. The source does not call removeFZ or clear 动作 there.
			helper.play_source_frame(85)
			helper.advance_timeline()
			assert(not helper.attacking and helper.source_action == 1)
			helper.activate({"x": 300, "y": 0, "facing": 1}, caster)
			assert(helper.source_action == 1, "natural completion changed the retained source action")
		helper.deactivate()
		assert(helper.source_action == 0)
		helper.activate({"x": 300, "y": 0, "facing": 1}, caster)
		# yfgj does not reinitialize the retained helper's 动作.
		assert(helper.source_action == 0)
		helper.free()
	caster.free()
	print("AI_HELPER_STATE_SMOKE_OK")
	quit()
