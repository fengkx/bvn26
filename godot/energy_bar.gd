class_name EnergyBar
extends Control

@export var mirrored: bool = false
var energy: float = 0.0:
	set(value):
		energy = clampf(value, 0.0, 300.0)
		queue_redraw()

const SEGMENT_COLORS := [Color("#168fd0"), Color("#19d892"), Color("#df2533")]


func _ready() -> void:
	custom_minimum_size = Vector2(145.0, 38.0)
	queue_redraw()


func _draw() -> void:
	# Source qitiao(): qi = round(ql)+1 drives the 0-100 bar frame, bs = floor(ql/100)+1
	# drives the stock counter. P1 is left, P2 is the mirrored right copy.
	var displayed := roundf(energy)
	var bar := Rect2(25.0, 15.0, 112.0, 12.0)
	var counter := Rect2(5.0, 6.0, 18.0, 29.0)
	if mirrored:
		bar.position.x = size.x - bar.end.x
		counter.position.x = size.x - counter.end.x
	draw_rect(bar.grow(2.0), Color("#d8f5ff"))
	draw_rect(bar.grow(1.0), Color("#15344e"))
	draw_rect(bar, Color("#020409"))
	var tier := mini(2, int(floorf(displayed / 100.0)))
	if displayed >= 100.0:
		draw_rect(bar, SEGMENT_COLORS[tier - 1])
	var progress := fmod(displayed, 100.0) / 100.0
	if displayed >= 300.0:
		progress = 1.0
	var fill := bar
	fill.size.x *= progress
	if mirrored:
		fill.position.x = bar.end.x - fill.size.x
	draw_rect(fill, SEGMENT_COLORS[tier])
	draw_rect(counter.grow(2.0), Color("#d8f5ff"))
	draw_rect(counter, SEGMENT_COLORS[tier].darkened(0.22))
	var font := ThemeDB.fallback_font
	var count := mini(3, int(floorf(displayed / 100.0)))
	var text_position := counter.position + Vector2(4.0, 22.0)
	draw_string(font, text_position, str(count), HORIZONTAL_ALIGNMENT_LEFT, -1.0, 20, Color("#07121c"))
