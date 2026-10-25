shader_type canvas_item;
render_mode unshaded, blend_disabled;
uniform sampler2D source_tex : filter_nearest;
uniform sampler2D coefficients : filter_nearest;
uniform sampler2D coordinates : filter_nearest;
uniform sampler2D phase : filter_nearest;

int signed_word(ivec2 p, int slot) {
    ivec4 bytes = ivec4(round(texelFetch(coefficients, ivec2(p.x * 8 + slot, p.y), 0) * 255.0));
    int high = bytes.a >= 128 ? bytes.a - 256 : bytes.a;
    return high * 16777216 + bytes.b * 65536 + bytes.g * 256 + bytes.r;
}

void fragment() {
    ivec2 p = ivec2(floor(UV * vec2(textureSize(coordinates, 0))));
    ivec4 c = ivec4(round(texelFetch(coordinates, p, 0)));
    if (c.a == 0) {
        COLOR = vec4(0.0);
    } else {
        ivec4 d = ivec4(round(texelFetch(phase, p, 0)));
        int qx = signed_word(p, 0) * c.x + signed_word(p, 1) * c.y + signed_word(p, 2) + signed_word(p, 3);
        int qy = signed_word(p, 4) * c.x + signed_word(p, 5) * c.y + signed_word(p, 6) + signed_word(p, 7);
        // The fixture proves positive numerators and signed-32-bit bounds before upload.
        int ix = (qx * d.y - d.x * 65536) / (d.y * 65536);
        int iy = (qy * d.w - d.z * 65536) / (d.w * 65536);
        COLOR = texelFetch(source_tex, ivec2(ix, iy + c.z), 0);
    }
}
