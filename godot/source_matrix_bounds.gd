class_name SourceMatrixBounds
extends RefCounted

const TWIPS_PER_PIXEL := 20


static func from_swf(matrix: Dictionary, offset: Vector2 = Vector2.ZERO) -> Dictionary:
	# Runtime clip offsets represent the amount applied to the original PlaceObject
	# translation; writing the corresponding AS2 _x/_y value stores integer twips.
	return from_components(
		float(matrix.get("scaleX", 1.0)),
		float(matrix.get("rotateSkew0", 0.0)),
		float(matrix.get("rotateSkew1", 0.0)),
		float(matrix.get("scaleY", 1.0)),
		int(matrix.get("translateX", 0)) + int(offset.x * TWIPS_PER_PIXEL),
		int(matrix.get("translateY", 0)) + int(offset.y * TWIPS_PER_PIXEL)
	)


static func from_components(
	a: float, b: float, c: float, d: float, tx_twips: int, ty_twips: int
) -> Dictionary:
	return {
		"a": _f32(a),
		"b": _f32(b),
		"c": _f32(c),
		"d": _f32(d),
		"tx": tx_twips,
		"ty": ty_twips,
	}


static func compose(parent: Dictionary, child: Dictionary) -> Dictionary:
	var pa := float(parent["a"])
	var pb := float(parent["b"])
	var pc := float(parent["c"])
	var pd := float(parent["d"])
	var ca := float(child["a"])
	var cb := float(child["b"])
	var cc := float(child["c"])
	var cd := float(child["d"])
	var a := _add(_mul(pa, ca), _mul(pc, cb))
	var b := _add(_mul(pb, ca), _mul(pd, cb))
	var c := _add(_mul(pa, cc), _mul(pc, cd))
	var d := _add(_mul(pb, cc), _mul(pd, cd))
	var tx_delta := _add(_mul(pa, float(child["tx"])), _mul(pc, float(child["ty"])))
	var ty_delta := _add(_mul(pb, float(child["tx"])), _mul(pd, float(child["ty"])))
	return from_components(
		a,
		b,
		c,
		d,
		round_ties_even(tx_delta) + int(parent["tx"]),
		round_ties_even(ty_delta) + int(parent["ty"])
	)


static func bounds_for_chain(rect_twips: Rect2i, leaf_to_root: Array[Dictionary]) -> Rect2i:
	if rect_twips.size.x <= 0 or rect_twips.size.y <= 0 or leaf_to_root.is_empty():
		return Rect2i()
	var matrix := leaf_to_root[0]
	for index in range(1, leaf_to_root.size()):
		matrix = compose(leaf_to_root[index], matrix)
	var points := [
		Vector2i(rect_twips.position.x, rect_twips.position.y),
		Vector2i(rect_twips.end.x, rect_twips.position.y),
		Vector2i(rect_twips.end.x, rect_twips.end.y),
		Vector2i(rect_twips.position.x, rect_twips.end.y),
	]
	var first := _transform_point(matrix, points[0])
	var minimum := first
	var maximum := first
	for index in range(1, points.size()):
		var point := _transform_point(matrix, points[index])
		minimum = Vector2i(mini(minimum.x, point.x), mini(minimum.y, point.y))
		maximum = Vector2i(maxi(maximum.x, point.x), maxi(maximum.y, point.y))
	return Rect2i(minimum, maximum - minimum)


static func round_ties_even(value: float) -> int:
	var lower := floori(value)
	var fraction := value - float(lower)
	if fraction < 0.5:
		return lower
	if fraction > 0.5:
		return lower + 1
	return lower if posmod(lower, 2) == 0 else lower + 1


static func _transform_point(matrix: Dictionary, point: Vector2i) -> Vector2i:
	var x := _add(_mul(float(matrix["a"]), float(point.x)),
		_mul(float(matrix["c"]), float(point.y)))
	var y := _add(_mul(float(matrix["b"]), float(point.x)),
		_mul(float(matrix["d"]), float(point.y)))
	return Vector2i(
		round_ties_even(x) + int(matrix["tx"]),
		round_ties_even(y) + int(matrix["ty"])
	)


static func _mul(left: float, right: float) -> float:
	return _f32(_f32(left) * _f32(right))


static func _add(left: float, right: float) -> float:
	return _f32(_f32(left) + _f32(right))


static func _f32(value: float) -> float:
	var packed := PackedFloat32Array([value])
	return float(packed[0])
