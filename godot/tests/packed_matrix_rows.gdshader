shader_type canvas_item;
render_mode unshaded, blend_disabled;
uniform sampler2D source_bytes : filter_nearest, repeat_disable;
uniform sampler2D matrix_words : filter_nearest, repeat_disable;
#include "res://tests/packed_matrix.gdshaderinc"
void fragment() {
	ivec2 size = textureSize(source_bytes, 0);
	ivec2 at = ivec2(floor(UV * vec2(size)));
	int width = int(texelFetch(matrix_words, ivec2(5, at.y), 0).r);
	if (at.x >= width) {
		COLOR = vec4(0.0);
	} else {
		ivec4 source = ivec4(round(texelFetch(source_bytes, at, 0) * 255.0));
		bool prefix = at.x < (width / 4) * 4;
		ivec4 mate = source;
		if (prefix) {
			int other = at.x + (at.x % 2 == 0 ? 1 : -1);
			mate = ivec4(round(texelFetch(source_bytes, ivec2(other, at.y), 0) * 255.0));
		}
		ivec4 c0 = ivec4(texelFetch(matrix_words, ivec2(0, at.y), 0));
		ivec4 c1 = ivec4(texelFetch(matrix_words, ivec2(1, at.y), 0));
		ivec4 c2 = ivec4(texelFetch(matrix_words, ivec2(2, at.y), 0));
		ivec4 c3 = ivec4(texelFetch(matrix_words, ivec2(3, at.y), 0));
		ivec4 offsets = ivec4(texelFetch(matrix_words, ivec2(4, at.y), 0));
		COLOR = vec4(matrix_packed(source, mate, prefix, c0, c1, c2, c3, offsets)) / 255.0;
	}
}
