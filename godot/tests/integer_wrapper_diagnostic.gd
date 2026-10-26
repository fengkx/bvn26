extends "res://tests/production_wrapper_diagnostic.gd"
# Preserve the inherited loader, PNG binding, buffers and readbacks. Replace only
# final normal composition in this opt-in diagnostic, never in a game scene.
func _initialize() -> void:
	node_added.connect(_bind_integer_composite)
	super._initialize()

func _bind_integer_composite(node: Node) -> void:
	if node.name != "Composite":
		return
	assert(node is Sprite2D and node.material is ShaderMaterial)
	var code: String = node.material.shader.code
	assert(code.contains("uniform bool cached_opacity"))
	assert(code.contains("COLOR = pixel;"))
	code = code.replace("shader_type canvas_item;", "shader_type canvas_item;\nrender_mode blend_disabled;\n#include \"res://tests/normal_composition.gdshaderinc\"\nuniform sampler2D screen_texture : hint_screen_texture, filter_nearest, repeat_disable;")
	code = code.replace("COLOR = pixel;", "ivec4 source = ivec4(round(vec4(pixel.rgb * pixel.a, pixel.a) * 255.0));\nivec4 back = ivec4(round(texture(screen_texture, SCREEN_UV) * 255.0));\nCOLOR = vec4(flash_normal_over(back, source)) / 255.0;")
	var shader := Shader.new()
	shader.code = code
	node.material.shader = shader
	# Copy the actual destination immediately before this composite is drawn.
	var copy := BackBufferCopy.new()
	copy.copy_mode = BackBufferCopy.COPY_MODE_VIEWPORT
	var parent := node.get_parent()
	parent.add_child.call_deferred(copy)
	parent.move_child.call_deferred(copy, node.get_index())
