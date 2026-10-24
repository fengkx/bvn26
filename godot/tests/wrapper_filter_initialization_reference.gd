extends SceneTree
const Fixture = preload("res://tests/rollback_fixture.gd")


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	for slot in [1, 2]:
		var selected := ["石田", "一护"] if slot == 1 else ["一护", "石田"]
		var fixture := Fixture.create(self, selected, ["鼬", "魂"])
		var game: Node = fixture.game
		var fighter: FighterRuntime = game.naruto if slot == 1 else game.ichigo
		# Native root observes one authored 0x0 Blur; BODY frame 1 removes it
		# before frames 2/3. Retaining the source array is independent of removal.
		var filters: Array = fighter._timeline.wrapper.filters
		assert(filters.size() == 1)
		assert(filters[0].type == "BLURFILTER")
		assert(filters[0].blurX == 0 and filters[0].blurY == 0 and filters[0].passes == 1)
		assert(fighter._source_placement_filters_cleared)
		var before: Dictionary = fixture.battle.save_state()
		assert(not before.has("error"), str(before))
		fighter._source_placement_filters_cleared = false
		assert(fixture.battle.load_state(before).is_empty())
		assert(fighter._source_placement_filters_cleared)
		Fixture.dispose(game, fixture.battle)
	print("WRAPPER_FILTER_INITIALIZATION_OK 2/2 slots; native initial filter retirement and rollback")
	quit()
