shader_type canvas_item;
render_mode blend_disabled;
#include "res://tests/native_cxform.gdshaderinc"
uniform sampler2D inputs : filter_nearest, repeat_disable;
uniform sampler2D opacities : filter_nearest, repeat_disable;
uniform sampler2D reciprocals : filter_nearest, repeat_disable;
void fragment() {
    ivec2 p = ivec2(FRAGCOORD.xy);
    ivec4 v = ivec4(texelFetch(inputs, p, 0));
    int opacity = int(texelFetch(opacities, p, 0).r);
    float reciprocal = texelFetch(reciprocals, ivec2(v.y, 0), 0).r;
    ivec4 result = native_byte_cxform(ivec4(ivec3(v.x), v.y), ivec3(v.z), ivec3(v.w), opacity, reciprocal);
    COLOR = vec4(result) / 255.0;
}
