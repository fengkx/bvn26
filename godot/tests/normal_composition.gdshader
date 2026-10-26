shader_type canvas_item;
render_mode blend_disabled;
#include "res://tests/normal_composition.gdshaderinc"
uniform sampler2D inputs : filter_nearest, repeat_disable;
uniform sampler2D parameters : filter_nearest, repeat_disable;
uniform sampler2D colors : filter_nearest, repeat_disable;
void fragment() {
    ivec2 pos = ivec2(FRAGCOORD.xy);
    int index = pos.y * 64 + pos.x;
    ivec4 back = ivec4(round(texelFetch(inputs, ivec2(0,index),0)*255.0));
    ivec4 middle = ivec4(round(texelFetch(inputs, ivec2(1,index),0)*255.0));
    ivec4 front = ivec4(round(texelFetch(inputs, ivec2(2,index),0)*255.0));
    ivec4 p = ivec4(round(texelFetch(parameters,ivec2(0,index),0)*255.0));
    int outer = p.y * 256 / 100;
    int combined = outer * (p.z * 256 / 100) / 256;
    int middle_multiplier = p.x == 2 ? combined : outer;
    if (p.w == 1) {
        middle = flash_vector_opacity(middle,ivec3(round(texelFetch(colors,ivec2(0,index),0).rgb*255.0)),middle_multiplier);
        front = flash_vector_opacity(front,ivec3(round(texelFetch(colors,ivec2(1,index),0).rgb*255.0)),combined);
    } else {
        middle = flash_bitmap_opacity(middle,middle_multiplier);
        front = flash_bitmap_opacity(front,combined);
    }
    COLOR = vec4(flash_normal_over(back,flash_normal_over(middle,front)))/255.0;
}
