extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const State = preload("res://simulation_state.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fixture := Fixture.create(self, ["鼬", "一护"], ["我爱罗", "魂"], "现世")
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	var fighter: FighterRuntime = game.naruto
	# The native placement probe leaves an undefined receiver/reference write
	# consumed, even when that name appears during later stopped-frame ticks.
	for missing_reference in [false, true]:
		fighter.start_action("站立")
		fighter.play_source_frame(1)
		var event: Dictionary = fighter._combat.clip_placements[1].duplicate(true)
		if missing_reference:
			# mian exists on both frames; zzzz only exists on the later frame.
			event.instance_name = "mian"
		assert(fighter.named_instance_origin("zzzz") == Vector2.INF)
		assert(missing_reference or fighter.named_instance_origin("kj1atm") == Vector2.INF)
		fighter._apply_clip_placement(event)
		var checkpoint: Dictionary = battle.save_state()
		assert(not checkpoint.has("error"))
		for replay in range(2):
			if replay == 1:
				assert(battle.load_state(checkpoint).is_empty())
			fighter.play_source_frame(313)
			assert(fighter.named_instance_origin(event.instance_name) != Vector2.INF)
			assert(fighter.named_instance_origin("zzzz") != Vector2.INF)
			for tick in range(3):
				fighter._apply_clip_placement(event)
			assert(fighter.instance_local_offset(event.instance_name) == Vector2.ZERO,
				"An undefined source write must not retry when its name appears")
		# Entering the action again is a new execution, not a permanent ban.
		fighter.start_action("砍技1")
		fighter.play_source_frame(313)
		fighter._apply_clip_placement(event)
		assert(fighter.instance_local_offset(event.instance_name) != Vector2.ZERO)
		var applied: Dictionary = battle.save_state()
		var expected: Dictionary = fighter._clip_placements_applied.duplicate(true)
		fighter._clip_placements_applied.clear()
		assert(battle.load_state(applied).is_empty())
		assert(fighter._clip_placements_applied == expected)
		assert(State.first_difference(applied, battle.save_state()).is_empty())
	Fixture.dispose(game, battle)
	await process_frame
	print("CLIP_PLACEMENT_ONCE_SMOKE_OK missing_target=true missing_reference=true rollback=true reentry=true")
	quit()
