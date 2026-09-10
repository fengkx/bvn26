class_name GameWorld
extends Node2D

# Source: scripts/main.json DefineSprite_1991/frame_1/DoAction.as
# and frame_7/DoAction.as (`mapSizeX`, `floorY`).
const TWEEN := 0.5
const SCALE_MIN := 0.8
const DISTANCE_LOCK := 700.0
const SCALE_REFERENCE := 1000.0
const VIEW_CENTER := 300.0
const VIEW_RIGHT := 620.0
const VIEW_Y_FLOOR := 400.0
const WALL_LEFT := 20.0
const WALL_RIGHT_INSET := 30.0
const MAP_SIZE_X := 1000.0
const CLOSE_SCALE := 2.0
const FAR_SCALE := 0.5

var focus: String = "all"
var map_size_x: float = MAP_SIZE_X
var lock_min: float = 0.0
var lock_max: float = 0.0
var game_x: float = 0.0
var game_y: float = VIEW_Y_FLOOR
var game_scale: float = 1.0


static func get_center(first: float, second: float) -> float:
	var low := minf(first, second)
	var high := maxf(first, second)
	return low + (high - low) / 2.0


static func compute_target(
	p1: Vector2,
	p2: Vector2,
	focus_mode: String,
	map_width: float = MAP_SIZE_X
) -> Dictionary:
	var center_x := 0.0
	var center_y := 0.0
	var scale := CLOSE_SCALE
	match focus_mode:
		"all":
			center_x = get_center(p1.x, p2.x)
			center_y = get_center(p1.y, p2.y)
			var span := maxf(absf(p1.x - p2.x), absf(p1.y - p2.y))
			var remain := SCALE_REFERENCE - span
			if remain <= 0.0:
				scale = FAR_SCALE
			else:
				scale = CLOSE_SCALE * (remain / SCALE_REFERENCE)
		"p1":
			center_x = p1.x
			center_y = p1.y
			scale = CLOSE_SCALE
		"p2":
			center_x = p2.x
			center_y = p2.y
			scale = CLOSE_SCALE
	if scale < SCALE_MIN:
		scale = SCALE_MIN
	var target_x := VIEW_CENTER - center_x * scale
	var target_y := VIEW_CENTER - center_y * scale
	var min_x := VIEW_RIGHT - map_width * scale
	if target_x > 0.0:
		target_x = 0.0
	if target_x < min_x:
		target_x = min_x
	if target_y < VIEW_Y_FLOOR:
		target_y = VIEW_Y_FLOOR
	return {"x": target_x, "y": target_y, "scale": scale}


func wall_max() -> float:
	return map_size_x - WALL_RIGHT_INSET


func snap(p1: Node2D, p2: Node2D) -> Dictionary:
	var target := compute_target(p1.position, p2.position, focus, map_size_x)
	game_x = float(target["x"])
	game_y = float(target["y"])
	game_scale = float(target["scale"])
	_apply()
	return target


func enter_frame(p1: Node2D, p2: Node2D, extras: Array = []) -> Dictionary:
	_clamp_walls([p1, p2] + extras)
	_update_distance_lock(p1, p2)
	var target := compute_target(p1.position, p2.position, focus, map_size_x)
	game_x += (float(target["x"]) - game_x) * TWEEN
	game_y += (float(target["y"]) - game_y) * TWEEN
	game_scale += (float(target["scale"]) - game_scale) * TWEEN
	_apply()
	return {
		"target": target,
		"x": game_x,
		"y": game_y,
		"scale": game_scale,
		"lock_min": lock_min,
		"lock_max": lock_max,
	}


func _apply() -> void:
	position = Vector2(game_x, game_y)
	scale = Vector2(game_scale, game_scale)


func _clamp_walls(bodies: Array) -> void:
	var left := WALL_LEFT
	var right := wall_max()
	for body in bodies:
		if body == null or not is_instance_valid(body):
			continue
		if body is HelperRuntime and not body.attacking:
			continue
		if body.position.x < left:
			body.position.x = left
		if body.position.x > right:
			body.position.x = right
		if body is FighterRuntime:
			body.source_hit_wall = not (body.position.x > left and body.position.x < right)


func _update_distance_lock(p1: Node2D, p2: Node2D) -> void:
	var distance := absf(p1.position.x - p2.position.x)
	if lock_min > 0.0 and lock_max > 0.0:
		if distance < DISTANCE_LOCK:
			lock_min = 0.0
			lock_max = 0.0
		else:
			p1.position.x = clampf(p1.position.x, lock_min, lock_max)
			p2.position.x = clampf(p2.position.x, lock_min, lock_max)
	elif distance >= DISTANCE_LOCK:
		lock_min = minf(p1.position.x, p2.position.x)
		lock_max = maxf(p1.position.x, p2.position.x)
