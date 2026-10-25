extends RefCounted
# Preserve authored vertices; accept only a cyclic start of the proven ordered edges.
static func matches(mask: Array, x: float, y: float, width: float, height: float) -> bool:
	if mask.size() != 4 or width <= 0 or height <= 0:
		return false
	for value in [x, y, width, height]:
		if not is_finite(value):
			return false
	var corners := [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]
	for start in 4:
		var same := true
		for i in 4:
			if mask[i] != corners[(i + start) % 4]:
				same = false
		if same:
			return true
	return false
