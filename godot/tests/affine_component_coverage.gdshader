shader_type canvas_item;
render_mode unshaded, blend_disabled;
uniform sampler2D source_tex : filter_nearest;
uniform sampler2D coefficients : filter_nearest;
uniform sampler2D coordinates : filter_nearest;


int signed_word(ivec2 p, int slot) {
    ivec4 bytes = ivec4(round(texelFetch(coefficients, ivec2(p.x * 8 + slot, p.y), 0) * 255.0));
    int high = bytes.a >= 128 ? bytes.a - 256 : bytes.a;
    return high * 16777216 + bytes.b * 65536 + bytes.g * 256 + bytes.r;
}

int floor_fixed(int value) {
    return value >= 0 ? value / 65536 : -((-value + 65535) / 65536);
}

void fragment() {
    ivec2 p = ivec2(floor(UV * vec2(textureSize(coordinates, 0))));
    ivec4 c = ivec4(round(texelFetch(coordinates, p, 0)));
    if (c.a == 0) {
        COLOR = vec4(0.0);
    } else {
        int qx = signed_word(p, 0) * c.x + signed_word(p, 1) * c.y + signed_word(p, 2) + signed_word(p, 3);
        int qy = signed_word(p, 4) * c.x + signed_word(p, 5) * c.y + signed_word(p, 6) + signed_word(p, 7);
        ivec2 sample_at = clamp(ivec2(floor_fixed(qx), floor_fixed(qy)), ivec2(0), textureSize(source_tex, 0) - ivec2(1));
        ivec4 bytes = ivec4(round(texelFetch(source_tex, sample_at, 0) * 255.0));
        COLOR = vec4(bytes * c.a / 16) / 255.0;
    }
}
