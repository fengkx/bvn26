/* Independent equivalent reciprocal constructions; no Flash ISA inference. */
#include <xmmintrin.h>
#include <stdint.h>
#include <stdio.h>

static uint32_t bits(float f) {
    union { float f; uint32_t u; } value = { .f = f };
    return value.u;
}
static float estimate(float input) {
    return _mm_cvtss_f32(_mm_rcp_ps(_mm_set1_ps(input)));
}
int main(void) {
    for (int a = 1; a < 256; a++) {
        volatile float alpha = (float)a;
        volatile float product = alpha * 255.0f;
        volatile float quotient = alpha / 255.0f;
        volatile float reciprocal = estimate(alpha);
        volatile float from_product = estimate(product);
        volatile float from_quotient = estimate(quotient);
        volatile float normalizer = estimate(255.0f);
        volatile float normalized = alpha * normalizer;
        float scalar = _mm_cvtss_f32(_mm_rcp_ss(_mm_set_ss(alpha)));
        printf("%d %08x %08x %08x %08x %08x %08x %08x\n", a,
               bits(1.0f / alpha), bits(reciprocal),
               bits(from_product * 255.0f), bits(from_quotient / 255.0f),
               bits(1.0f / product * 255.0f), bits(scalar),
               bits(estimate(normalized) * normalizer));
    }
    return 0;
}
