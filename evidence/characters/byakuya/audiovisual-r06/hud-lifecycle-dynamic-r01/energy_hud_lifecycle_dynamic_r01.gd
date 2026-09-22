extends SceneTree

var bar: EnergyBar

func _init() -> void:
	bar = EnergyBar.new()
	bar.name = "EnergyLifecycleProbe"
	bar.size = Vector2(240.0, 80.0)
	root.add_child.call_deferred(bar)
	call_deferred("_run")

func _read(name: String):
	return bar.get(name)

func _assert_eq(actual, expected, label: String) -> void:
	if actual != expected:
		push_error("HUD_LIFECYCLE_FAIL %s actual=%s expected=%s" % [label, str(actual), str(expected)])
		quit(2)

func _run() -> void:
	await process_frame
	bar.energy = 300.0
	_assert_eq(_read("_qt_child_frame"), 1, "energy_enter_301_child1")
	bar.energy = 300.0
	_assert_eq(_read("_qt_child_frame"), 1, "same_energy_no_advance")
	bar.advance_display_tick(100)
	_assert_eq(_read("_qt_child_frame"), 1, "tick100_child1")
	bar.advance_display_tick(100)
	_assert_eq(_read("_qt_child_frame"), 1, "duplicate_tick100_no_advance")
	for tick in range(101, 110):
		bar.advance_display_tick(tick)
		_assert_eq(_read("_qt_child_frame"), tick - 99, "tick%d_child" % tick)
	bar.advance_display_tick(110)
	_assert_eq(_read("_qt_child_frame"), 1, "tick110_wrap_child1")
	bar.energy = 299.0
	bar.advance_display_tick(111)
	_assert_eq(_read("_qt_child_frame"), 1, "leave_301_resets_child1")
	bar.energy = 300.0
	_assert_eq(_read("_qt_child_frame"), 1, "reenter_301_before_tick_child1")
	bar.advance_display_tick(112)
	_assert_eq(_read("_qt_child_frame"), 1, "reenter_301_child1")
	print("HUD_LIFECYCLE_DYNAMIC_OK")
	print("child_sequence=1,2,3,4,5,6,7,8,9,10,1; duplicate_tick_and_same_energy_checked")
	quit(0)
