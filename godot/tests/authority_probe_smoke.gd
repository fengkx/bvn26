extends SceneTree

const Fixture = preload("res://tests/rollback_fixture.gd")
const Probe = preload("res://authority_probe.gd")
const Selection = preload("res://authority_host_selection.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var fixture := Fixture.create(self, ["鸣人", "一护"], ["我爱罗", "魂"], "现世")
	fixture.battle.close()
	var probe := Probe.new()
	var report := await probe.run(fixture.game, func() -> bool: return true)
	assert(Selection.valid(report), str(report))
	assert(fixture.game.physics_tick == 240)
	fixture.game._goto_menu()
	fixture.game.free()
	var fresh := Fixture.create(self, ["鸣人", "一护"], ["我爱罗", "魂"], "现世")
	assert(fresh.game.physics_tick == 0)
	Fixture.dispose(fresh.game, fresh.battle)
	print("AUTHORITY_PROBE_OK isolated=true measured_samples=120 not_a_pass=true")
	await create_timer(0.1).timeout
	quit()
