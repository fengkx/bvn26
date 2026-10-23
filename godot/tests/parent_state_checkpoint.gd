extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var fixture := Fixture.create(self, ["白哉", "一护"], ["鼬", "魂"])
	var fighter: FighterRuntime = fixture.game.naruto
	assert(fighter.read_parent_field("万解") == false)
	var snapshot: Dictionary = fixture.battle.save_state()
	assert(not snapshot.has("error"), str(snapshot))
	fighter.write_parent_field("万解", true)
	assert(fixture.battle.load_state(snapshot).is_empty())
	assert(fighter.read_parent_field("万解") == false, "Rollback lost parent state ownership")
	fighter.write_parent_field("万解", true)
	var changed: Dictionary = fixture.battle.save_state()
	fighter.write_parent_field("万解", false)
	assert(fixture.battle.load_state(changed).is_empty())
	assert(fighter.read_parent_field("万解") == true)
	print("PARENT_STATE_CHECKPOINT_OK false_and_true_restored")
	Fixture.dispose(fixture.game, fixture.battle)
	await process_frame
	quit()
