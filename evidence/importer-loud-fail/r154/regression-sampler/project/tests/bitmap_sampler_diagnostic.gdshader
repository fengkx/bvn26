shader_type canvas_item;
render_mode blend_disabled;
uniform sampler2D c00 : filter_nearest;
uniform sampler2D c10 : filter_nearest;
uniform sampler2D c01 : filter_nearest;
uniform sampler2D c11 : filter_nearest;
uniform sampler2D parameters : filter_nearest;
void fragment() {
    vec4 a = floor(texture(c00, UV) * 255.0 + 0.5);
    vec4 b = floor(texture(c10, UV) * 255.0 + 0.5);
    vec4 c = floor(texture(c01, UV) * 255.0 + 0.5);
    vec4 d = floor(texture(c11, UV) * 255.0 + 0.5);
    vec4 p = floor(texture(parameters, UV) * 255.0 + 0.5);
    float x = p.r; float y = p.g;
    vec4 result;
    if (p.b < 0.5) {
        float w0 = floor((256.0-x)*(256.0-y)/256.0);
        float w1 = floor(x*(256.0-y)/256.0);
        float w2 = floor((256.0-x)*y/256.0);
        result = floor((a*w0+b*w1+c*w2+d*(256.0-w0-w1-w2))/256.0);
    } else if (p.b < 1.5) {
        vec4 left = floor((a*(256.0-y)+c*y)/256.0);
        vec4 right = floor((b*(256.0-y)+d*y)/256.0);
        result = floor((left*(256.0-x)+right*x)/256.0);
    } else {
        vec4 top = floor((a*(256.0-x)+b*x)/256.0);
        vec4 bottom = floor((c*(256.0-x)+d*x)/256.0);
        result = floor((top*(256.0-y)+bottom*y)/256.0);
    }
    // Existing references draw onto opaque black, so RGB is premultiplied and A=255.
    if (p.a > 0.5) {
        // Native getPixel32 readback candidate: quantized reciprocal, nearest/ties down.
        // This encoding step is not a production framebuffer blending rule.
        int alpha = int(result.a);
        result.rgb = alpha > 0 ? vec3((ivec3(result.rgb) * (65280 / alpha) + ivec3(127)) / 256) : vec3(0.0);
    } else {
        result.a = 255.0;
    }
    COLOR = result / 255.0;
}
