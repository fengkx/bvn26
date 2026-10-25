shader_type canvas_item;
render_mode unshaded, blend_disabled;
uniform sampler2D source_tex : filter_nearest;
uniform sampler2D ax : filter_nearest;
uniform sampler2D bx : filter_nearest;
uniform sampler2D tx : filter_nearest;
uniform sampler2D ox : filter_nearest;
uniform sampler2D ay : filter_nearest;
uniform sampler2D by : filter_nearest;
uniform sampler2D ty : filter_nearest;
uniform sampler2D oy : filter_nearest;
uniform sampler2D coordinates : filter_nearest;
uniform sampler2D phase : filter_nearest;

int signed_word(sampler2D values, ivec2 p) {
    ivec4 bytes = ivec4(round(texelFetch(values, p, 0) * 255.0));
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
        int qx = signed_word(ax, p) * c.x + signed_word(bx, p) * c.y + signed_word(tx, p) + signed_word(ox, p);
        int qy = signed_word(ay, p) * c.x + signed_word(by, p) * c.y + signed_word(ty, p) + signed_word(oy, p);
        // The fixture proves positive numerators and signed-32-bit bounds before upload.
        int ix = (qx * d.y - d.x * 65536) / (d.y * 65536);
        int iy = (qy * d.w - d.z * 65536) / (d.w * 65536);
        COLOR = texelFetch(source_tex, ivec2(ix, iy + c.z), 0);
    }
}
