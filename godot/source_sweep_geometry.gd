extends RefCounted


static func horizontal_sweep_fraction(moving: Rect2, target: Rect2, delta_x: float) -> float:
	if is_zero_approx(delta_x):
		return -1.0
	if moving.end.y <= target.position.y or moving.position.y >= target.end.y:
		return -1.0
	var entry: float
	var leave: float
	if delta_x > 0.0:
		entry = (target.position.x - moving.end.x) / delta_x
		leave = (target.end.x - moving.position.x) / delta_x
	else:
		entry = (target.end.x - moving.position.x) / delta_x
		leave = (target.position.x - moving.end.x) / delta_x
	if entry > leave or leave < 0.0 or entry > 1.0:
		return -1.0
	return clampf(entry, 0.0, 1.0)
