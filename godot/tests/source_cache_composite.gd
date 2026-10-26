extends "res://tests/source_cache_filter.gd"
# Keep the same buffers; replace only final copy with explicit ordinary composition.
const NORMAL = preload("res://tests/nested_integer_composite.gdshader")

func _initialize() -> void:
	node_added.connect(_bind_destination)
	super._initialize()

func _bind_destination(node: Node) -> void:
	if node is SubViewport and node.get_parent() == root and node.size == Vector2i(600, 400):
		var background := ColorRect.new()
		background.size = Vector2(600, 400)
		background.color = Color(96.0 / 255, 96.0 / 255, 96.0 / 255, 1)
		node.add_child.call_deferred(background)
		node.move_child.call_deferred(background, 0)
	if node.name == "Composite" and node is Sprite2D:
		var material := ShaderMaterial.new()
		material.shader = NORMAL
		node.material = material
		var copy := BackBufferCopy.new()
		copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
		var parent := node.get_parent()
		parent.add_child.call_deferred(copy)
		parent.move_child.call_deferred(copy, node.get_index())
