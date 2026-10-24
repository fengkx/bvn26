/* Independent input-normalization measurements; no native pixels or ISA claim. */
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
    volatile float rounded_unit = 1.0f / 255.0f;
    volatile float estimated_unit = estimate(255.0f);
    for (int i = 1; i < 256; i++) {
        volatile float input = (float)i;
        volatile float divided = input / 255.0f;
        volatile float multiplied = input * rounded_unit;
        volatile float estimated = input * estimated_unit;
        printf("%d %08x %08x %08x %08x %08x %08x\n", i,
               bits(divided), bits(estimate(divided)),
               bits(multiplied), bits(estimate(multiplied)),
               bits(estimated), bits(estimate(estimated)));
    }
    return 0;
}
