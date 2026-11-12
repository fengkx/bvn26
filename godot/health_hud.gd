class_name HealthHud
extends Control

const DIRECTORY := "res://generated/main/health"
const PORTRAITS := "res://generated/main/helper_portraits"
var presentation_health: Array = []
var presentation_countdown: Dictionary = {}
var countdown: MatchCountdown
var spec: Dictionary
var portraits: Dictionary
var textures: Dictionary = {}
var portrait_labels: Array = ["鸣人", "一护"]
var portrait_textures: Array[Texture2D] = []
var warning_textures: Array[Texture2D] = []
var fighters: Array[FighterRuntime] = []
var trail: Array[float] = [100.0, 100.0]
var low_frame: Array[int] = [0, 0]
var low_health: Array[bool] = [false, false]
var win_frames := PackedInt32Array([1, 1])


func _ready() -> void:
	if spec != null and not spec.is_empty(): return
	spec = JSON.parse_string(FileAccess.get_file_as_string(DIRECTORY + "/presentation.json"))
	portraits = JSON.parse_string(FileAccess.get_file_as_string(PORTRAITS + "/presentation.json"))
	for label in portrait_labels:
		portrait_textures.append(load("%s/%s" % [PORTRAITS, portraits["portraits"][label]["texture"]]))
	for frame in range(1, 21):
		warning_textures.append(load("%s/low-%d.png" % [DIRECTORY, frame]))
	for id: String in spec["layers"]:
		textures[id] = load("%s/%s.png" % [DIRECTORY, id])


func set_fighter_portraits(labels: Array) -> void:
	portrait_labels = labels.duplicate()
	portrait_textures.clear()
	for label in portrait_labels:
		portrait_textures.append(load("%s/%s" % [PORTRAITS, portraits["portraits"][label]["texture"]]))
	queue_redraw()


func reset() -> void:
	trail = [100.0, 100.0]
	low_frame = [0, 0]
	low_health = [false, false]
	queue_redraw()


func refresh() -> void:
	if fighters.size() == 2 and fighters[0].health > 0 and fighters[1].health > 0:
		for i in 2:
			var percent := fighters[i].health / fighters[i].max_health * 100.0
			if fighters[i].hits == 0:
				trail[i] = trail[i] - fighters[i].max_health / 500.0 if trail[i] > percent else percent
			if low_health[i]:
				low_frame[i] = (low_frame[i] + 1) % 20
			if percent < 20:
				low_health[i] = true
	queue_redraw()


func _matrix(placement: Dictionary) -> Transform2D:
	var m: Dictionary = placement.get("matrix", placement)
	return Transform2D(Vector2(float(m.get("scaleX", 1)), float(m.get("rotateSkew0", 0))),
		Vector2(float(m.get("rotateSkew1", 0)), float(m.get("scaleY", 1))),
		Vector2(float(m.get("translateX", 0)), float(m.get("translateY", 0))) / 20.0)


func set_wins(p1_frame: int, p2_frame: int) -> void:
	for frame in [p1_frame, p2_frame]:
		assert(spec["win_frames"].has(str(frame)), "Win counter is an authored HUD frame")
	win_frames = PackedInt32Array([p1_frame, p2_frame])
	queue_redraw()


func win_placements(side: int) -> Array:
	assert(side in [0, 1])
	return spec["win_frames"][str(win_frames[side])]


func _layer(id: int, transform_matrix: Transform2D, alpha: float = 1.0, texture_override: Texture2D = null) -> void:
	var bounds: Dictionary = spec["layers"][str(id)]
	var rect := Rect2(float(bounds["Xmin"]) / 20, float(bounds["Ymin"]) / 20,
		float(bounds["Xmax"] - bounds["Xmin"]) / 20, float(bounds["Ymax"] - bounds["Ymin"]) / 20)
	draw_set_transform_matrix(transform_matrix)
	draw_texture_rect(texture_override if texture_override != null else textures[str(id)], rect, false, Color(1, 1, 1, alpha))


func _draw() -> void:
	if spec.is_empty() or (fighters.size() != 2 and presentation_health.size() != 2):
		return
	var base := _matrix(spec["outer"]) * _matrix(spec["placement"])
	for part: Dictionary in spec["parts"]:
		var name_string := str(part.get("name", ""))
		var transform_matrix := base * _matrix(part)
		var index := 1 if name_string.begins_with("p2") else 0
		if name_string.ends_with("xt"):
			for bar: Dictionary in spec["bar_parts"]:
				var bar_name := str(bar.get("name", ""))
				var local := _matrix(bar)
				if bar_name == "win":
					for marker: Dictionary in win_placements(index):
						_layer(int(marker.character_id), transform_matrix * local * _matrix(marker))
				elif bar_name == "kk":
					var warning: Texture2D = warning_textures[low_frame[index]] if low_health[index] else null
					_layer(1787, transform_matrix * local, 1.0, warning)
				elif bar_name == "bar" or bar_name == "bar2":
					var maximum := float(presentation_health[index][1]) if not presentation_health.is_empty() else fighters[index].max_health
					var current := float(presentation_health[index][0]) if not presentation_health.is_empty() else fighters[index].health
					var hp := current if bar_name == "bar" else trail[index] * maximum / 100.0
					# Keep the authored fill direction while applying the HP percentage.
					local.x *= clampf(hp / maximum, 0, 1)
					if hp > 0:
						_layer(1792 if bar_name == "bar" else 591, transform_matrix * local, 1.0 if bar_name == "bar" else 205.0 / 256)
		elif name_string.ends_with("head"):
			_layer(1796, transform_matrix)
			var portrait: Dictionary = portraits["portraits"][portrait_labels[index]]
			var texture: Texture2D = portrait_textures[index]
			var bitmap := _matrix(portrait["matrix"])
			bitmap.x /= 20.0
			bitmap.y /= 20.0
			var placement := _matrix(spec["head_parts"][2])
			var inverse := (placement * bitmap).affine_inverse()
			var points := PackedVector2Array()
			var uv := PackedVector2Array()
			for point: Array in spec["mask"]:
				var vertex := Vector2(point[0], point[1])
				points.append(vertex)
				uv.append((inverse * vertex) / texture.get_size())
			draw_set_transform_matrix(transform_matrix)
			draw_polygon(points, PackedColorArray([Color.WHITE]), uv, texture)
		elif int(part.character_id) == 1813 and (countdown != null or not presentation_countdown.is_empty()):
			var unlimited: bool = presentation_countdown.unlimited if not presentation_countdown.is_empty() else countdown.unlimited
			var digits: Dictionary = presentation_countdown.digits if not presentation_countdown.is_empty() else countdown.digit_frames
			var timer_spec: Dictionary = spec["timer"]
			var parts: Array = timer_spec.unlimited_parts if unlimited else timer_spec.initial_parts
			for timer_part: Dictionary in parts:
				var local := transform_matrix * _matrix(timer_part)
				if unlimited:
					_layer(int(timer_part.character_id), local)
				else:
					var frame := str(digits[timer_part.name])
					for glyph: Dictionary in timer_spec.digit_frames[frame]:
						_layer(int(glyph.character_id), local * _matrix(glyph))
	draw_set_transform_matrix(Transform2D.IDENTITY)
