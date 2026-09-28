extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const State = preload("res://simulation_state.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var fixture := Fixture.create(self)
	var game: Node = fixture.game
	var battle: RefCounted = fixture.battle
	var cold_snapshot: Dictionary = battle.save_state()
	assert(not cold_snapshot.has("error"), str(cold_snapshot))
	assert(not battle.checkpoint._immutable_fields.is_empty(), "Fixture did not populate immutable field cache")
	var warm_snapshot: Dictionary = battle.save_state()
	assert(not warm_snapshot.has("error"), str(warm_snapshot))
	assert(State.first_difference(cold_snapshot, warm_snapshot).is_empty(), "Warm immutable cache changed the complete checkpoint")
	assert(cold_snapshot.owners.battle.owners.graph == warm_snapshot.owners.battle.owners.graph, "Warm immutable cache changed raw graph bytes")
	Fixture.dispose(game, battle)
	await process_frame
	print("BATTLE_CHECKPOINT_IMMUTABLE_CACHE_SMOKE_OK warm_snapshot_exact=true")
	quit()
