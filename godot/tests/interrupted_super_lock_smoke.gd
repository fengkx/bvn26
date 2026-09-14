extends SceneTree


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var sasuke := await _fighter("sasuke", "p2")
	var yulong := await _fighter("yulong", "p1")
	var shared := SuperRuntime.new()
	sasuke.super_runtime = shared
	yulong.super_runtime = shared
	sasuke.opponent = yulong
	yulong.opponent = sasuke

	# A real non-guard hit interrupts the pre-bsd preparation before source
	# frame 1 can run its `bs = 0` initializer.
	sasuke.start_action("必杀")
	_set_bs(sasuke, 1)
	sasuke.receive_attack(_attack(), 1)
	assert(sasuke.action == "被打")
	assert(sasuke.bs == 0 and sasuke.ai_source_state.read_field("bs") == 0)
	assert(not shared.zhanting)

	# A prepared super remains locked until an actual interruption.
	sasuke.start_action("必杀")
	_set_bs(sasuke, 1)
	assert(sasuke.bs == 1)

	# Guarding does not interrupt the prepared source action.
	sasuke.start_action("防御")
	_set_bs(sasuke, 1)
	sasuke.guarding = true
	sasuke.receive_attack(_attack(), 1)
	assert(sasuke.bs == 1 and sasuke.ai_source_state.read_field("bs") == 1)
	sasuke.guarding = false

	# The shared black-stage state and user pause both protect their own pause.
	shared.apply({"op": "super_start", "kind": "bsd"}, sasuke, yulong)
	assert(shared.zhanting and sasuke.bs == 1)
	shared.apply({"op": "super_end", "kind": "cbsw"}, yulong, sasuke)
	assert(shared.zhanting and sasuke.bs == 1,
		"An active opponent super must still block the other super's end")
	sasuke.receive_attack(_attack(), 1)
	assert(shared.zhanting and sasuke.bs == 1)
	shared.zhanting = false
	sasuke.root_zhanting = false
	yulong.root_zhanting = false
	shared.game_paused = true
	_set_bs(sasuke, 1)
	sasuke.receive_attack(_attack(), 1)
	assert(shared.game_paused and sasuke.bs == 1)
	shared.game_paused = false

	# The same interruption rule applies to another fighter's source state.
	var minren := await _fighter("minren", "p2")
	minren.super_runtime = shared
	minren.opponent = yulong
	minren.start_action("必杀")
	_set_bs(minren, 1)
	minren.receive_attack(_attack(), 1)
	assert(minren.action == "被打")
	assert(minren.bs == 0 and minren.ai_source_state.read_field("bs") == 0)

	print("INTERRUPTED_SUPER_LOCK_SMOKE_OK")
	for fighter in [sasuke, yulong, minren]:
		fighter.queue_free()
	await process_frame
	quit()


func _fighter(id: String, slot: String) -> FighterRuntime:
	var fighter := FighterRuntime.new()
	fighter.fighter_directory = "res://generated/fighters/" + id
	fighter.player_slot = slot
	root.add_child(fighter)
	await process_frame
	return fighter


func _set_bs(fighter: FighterRuntime, value: int) -> void:
	fighter.bs = value
	fighter.ai_source_state.values["bs"] = value


func _attack() -> Dictionary:
	return {
		"damage": 10.0,
		"impact_strength": 0,
		"vertical_impulse": 0.0,
		"horizontal_impulse": 0.0,
		"hitstun_ms": 1000,
		"reaction_label": "被打",
	}
