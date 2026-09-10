shader_type canvas_item;
render_mode unshaded;

uniform int sample_grid = 4;
uniform vec2 output_size;

void fragment() {
	vec2 origin = floor(UV * output_size) * float(sample_grid);
	vec4 sum = vec4(0.0);
	for (int y = 0; y < sample_grid; y++) {
		for (int x = 0; x < sample_grid; x++) {
			sum += texture(TEXTURE, (origin + vec2(float(x), float(y)) + 0.5) * TEXTURE_PIXEL_SIZE);
		}
	}
	COLOR = sum / float(sample_grid * sample_grid);
}
