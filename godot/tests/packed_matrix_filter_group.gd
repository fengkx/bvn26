extends "res://filter_group.gd"
# Keep allocation and the original pass input; replace only diagnostic arithmetic.
const PACKED_SHADER = preload("res://tests/packed_matrix_filter.gdshader")
func _filter_pass(input: Texture2D, uniforms: Dictionary, filter_index: int = -1, axis: int = 0) -> Texture2D:
	assert(get_meta("production_admitted", true) == false)
	assert(uniforms.operation == 2)
	var filters: Array = get_meta("flash_filters")
	assert(filters.size() == 1 and filters[0].type == "COLORMATRIXFILTER")
	assert(get_meta("packed_matrix_source") == filters[0].matrix)
	var words: Array = get_meta("packed_matrix_words")
	assert(words.size() == 4)
	var result := super._filter_pass(input, uniforms, filter_index, axis)
	var viewport: SubViewport = get_child(get_child_count() - 1)
	var sprite: Sprite2D = viewport.get_child(0)
	assert(sprite.texture == input and viewport.size == $Contents.size)
	var material: ShaderMaterial = sprite.material
	assert(material.shader == FILTER_SHADER)
	material.shader = PACKED_SHADER
	for column in 5:
		var value := Vector4i(words[0][column], words[1][column], words[2][column], words[3][column])
		material.set_shader_parameter("packed_offsets" if column == 4 else "matrix_c%d" % column, value)
	return result
