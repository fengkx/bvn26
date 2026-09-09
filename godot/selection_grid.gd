class_name SelectionGrid
extends RefCounted

# Source shared left/right/up/down in Sprite 1477/1480/1505.
static func move(cards: Array, point: Vector2i, direction: String, accept: Callable) -> void:
	var horizontal := direction == "left" or direction == "right"
	var step := -1 if direction == "left" or direction == "up" else 1
	var low := 9999
	var high := 0
	for card: Dictionary in cards:
		var value := int(card.grid[0 if horizontal else 1])
		low = mini(low, value)
		high = maxi(high, value)
	var start := point.x if horizontal else point.y
	if step < 0 and start <= low:
		start = high + 1
	elif step > 0 and start >= high:
		start = low - 1
	for offset in [0, -2, 2]:
		var coordinate := start + step
		while coordinate >= low and coordinate <= high:
			var candidate := Vector2i(coordinate, point.y + offset) if horizontal else Vector2i(point.x + offset, coordinate)
			if accept.call(candidate):
				return
			coordinate += step
