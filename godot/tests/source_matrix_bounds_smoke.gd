extends SceneTree

const SourceBounds = preload("res://source_matrix_bounds.gd")
const ShapeBounds := Rect2i(0, 0, 1319, 810)


func _initialize() -> void:
	_assert_ties_even()
	_assert_skew_mapping()
	_assert_reference_chains()
	print("SOURCE_MATRIX_BOUNDS_SMOKE_OK")
	quit()


func _assert_ties_even() -> void:
	assert(SourceBounds.round_ties_even(0.5) == 0)
	assert(SourceBounds.round_ties_even(1.5) == 2)
	assert(SourceBounds.round_ties_even(-0.5) == 0)
	assert(SourceBounds.round_ties_even(-1.5) == -2)
	assert(SourceBounds.round_ties_even(2.5) == 2)
	assert(SourceBounds.round_ties_even(-2.5) == -2)
	var half_scale := _matrix(0.5, 0.0, 0.0, 0.5, 0, 0)
	var half_twip := _matrix(1.0, 0.0, 0.0, 1.0, 1, -1)
	var composed := SourceBounds.compose(half_scale, half_twip)
	assert(composed["tx"] == 0 and composed["ty"] == 0)
	var one_and_half := _matrix(1.0, 0.0, 0.0, 1.0, 3, -3)
	composed = SourceBounds.compose(half_scale, one_and_half)
	assert(composed["tx"] == 2 and composed["ty"] == -2)


func _assert_skew_mapping() -> void:
	var source := SourceBounds.from_swf({
		"scaleX": 1.0,
		"rotateSkew0": 0.25,
		"rotateSkew1": -0.5,
		"scaleY": 1.0,
		"translateX": 0,
		"translateY": 0,
	})
	var result := SourceBounds.bounds_for_chain(Rect2i(0, 0, 20, 10), [source])
	assert(result == Rect2i(-5, 0, 25, 15), "SWF rotateSkew0/1 mapping changed: %s" % result)


func _assert_reference_chains() -> void:
	# Full local chains were sampled from Flash at Rukia hierarchy r02 tick 14.
	var rukia_receiver := _bounds([
		_matrix(0.4037933349609375, 0.0, 0.0, 1.10406494140625, -315, -416),
		_matrix(1.0, 0.0, 0.0, 1.0, 20, -479),
		_matrix(-1.0, 0.0, 0.0, 1.0, 7000, -500),
		_matrix(1.90496826171875, 0.0, 0.0, 1.90496826171875, -6430, 7999),
		_matrix(1.0, 0.0, 0.0, 1.0, 0, 0),
	])
	var rukia_attack := _bounds([
		_matrix(0.6883697509765625, 0.0, 0.0, 0.2512664794921875, -335, 179),
		_matrix(1.0, 0.0, 0.0, 1.0, -11, -474),
		_matrix(1.0, 0.0, 0.0, 1.0, 6200, -500),
		_matrix(1.90496826171875, 0.0, 0.0, 1.90496826171875, -6430, 7999),
		_matrix(1.0, 0.0, 0.0, 1.0, 0, 0),
	])
	assert(rukia_receiver == Rect2i(6452, 5342, 1015, 1704),
		"Rukia receiver root box differs from Flash r02: %s" % rukia_receiver)
	assert(rukia_attack == Rect2i(4722, 6485, 1730, 388),
		"Rukia attack root box differs from Flash r02: %s" % rukia_attack)
	assert(_boxes_intersect(rukia_receiver, rukia_attack), "Rukia source pair must touch")

	# The controlled R13 r04 capture has the same complete source matrix chain.
	var r13_sensor := _bounds([
		_matrix(2.1915283203125, 0.0, 0.0, 5.936614990234375, -1515, -4258),
		_matrix(1.0, 0.0, 0.0, 1.0, 10, 9),
		_matrix(1.0, 0.0, 0.0, 1.0, 20, -479),
		_matrix(1.0, 0.0, 0.0, 1.0, 15122, -500),
		_matrix(1.4739990234375, 0.0, 0.0, 1.4739990234375, -8905, 7999),
		_matrix(1.0, 0.0, 0.0, 1.0, 0, 0),
	])
	var r13_target := _bounds([
		_matrix(0.4261322021484375, 0.0, 0.0, 1.2910308837890625, -295, -537),
		_matrix(1.0, 0.0, 0.0, 1.000701904296875, -13, -478),
		_matrix(-1.0, 0.0, 0.0, 1.0, 16782, -500),
		_matrix(1.4739990234375, 0.0, 0.0, 1.4739990234375, -8905, 7999),
		_matrix(1.0, 0.0, 0.0, 1.0, 0, 0),
	])
	assert(r13_sensor == Rect2i(11196, 293, 4261, 7088),
		"R13 sensor root box differs from Flash r04: %s" % r13_sensor)
	assert(r13_target == Rect2i(15458, 5766, 828, 1542),
		"R13 target root box differs from Flash r04: %s" % r13_target)
	assert(not _boxes_intersect(r13_sensor, r13_target), "R13 source pair has a one-twip gap")


func _bounds(leaf_to_root: Array[Dictionary]) -> Rect2i:
	return SourceBounds.bounds_for_chain(ShapeBounds, leaf_to_root)


func _matrix(a: float, b: float, c: float, d: float, tx: int, ty: int) -> Dictionary:
	return SourceBounds.from_components(a, b, c, d, tx, ty)


func _boxes_intersect(first: Rect2i, second: Rect2i) -> bool:
	return not (
		first.end.x < second.position.x
		or second.end.x < first.position.x
		or first.end.y < second.position.y
		or second.end.y < first.position.y
	)
