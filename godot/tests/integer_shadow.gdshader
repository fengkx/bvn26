shader_type canvas_item;
render_mode blend_disabled;
uniform sampler2D original_texture : filter_nearest, repeat_disable;
uniform ivec4 color_bytes;
uniform int strength_256;
uniform vec2 shadow_offset;
uniform bool apply_filter_api = true;
uniform bool source_hidden = false;

int alpha_at(sampler2D image, ivec2 p) {
    if (any(lessThan(p, ivec2(0))) || any(greaterThanEqual(p, textureSize(image, 0)))) { return 0; }
    return int(floor(texelFetch(image, p, 0).a * 255.0 + 0.5));
}

void fragment() {
    ivec2 p = ivec2(floor(UV / TEXTURE_PIXEL_SIZE));
    vec2 scaled = shadow_offset * 256.0;
    ivec2 phase = ivec2(apply_filter_api ? roundEven(scaled) : sign(scaled) * floor(abs(scaled) + 0.5));
    ivec2 whole = ivec2(floor(vec2(phase) / 256.0));
    ivec2 f = phase - whole * 256;
    int w0 = (256-f.x)*(256-f.y)/256;
    int w1 = f.x*(256-f.y)/256;
    int w2 = (256-f.x)*f.y/256;
    int w3 = 256-w0-w1-w2;
    ivec2 q = p-whole;
    int a = (alpha_at(TEXTURE,q)*w0 + alpha_at(TEXTURE,q-ivec2(1,0))*w1 + alpha_at(TEXTURE,q-ivec2(0,1))*w2 + alpha_at(TEXTURE,q-ivec2(1,1))*w3)/256;
    int gain = min(255, a*strength_256/256);
    ivec4 premult = ivec4((color_bytes.rgb*color_bytes.a*2+ivec3(255))/510, color_bytes.a);
    ivec4 shadow = (premult*gain*2+ivec4(255))/510;
    ivec4 base = ivec4(floor(texelFetch(original_texture,p,0)*255.0+0.5));
    COLOR = vec4(source_hidden ? shadow : base+shadow*(256-base.a)/256)/255.0;
}
