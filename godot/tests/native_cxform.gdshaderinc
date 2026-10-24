// Diagnostic byte-domain construction; reciprocal texture is independently measured.
ivec4 native_byte_cxform(ivec4 source, ivec3 multiplier, ivec3 offset,
                       int opacity, float reciprocal) {
    if (source.a == 0) {
        return ivec4(0);
    }
    vec3 straight = vec3(source.rgb) * reciprocal;
    vec3 transformed = straight * (vec3(multiplier) / 256.0);
    transformed = clamp(transformed + vec3(offset), vec3(0.0), vec3(255.0));
    float output_alpha = float(source.a) * (float(opacity) / 256.0);
    float normalize = uintBitsToFloat(0x3b808081u);
    vec3 premultiplied = transformed * (output_alpha * normalize);
    return ivec4(ivec3(premultiplied), source.a * opacity / 256);
}
