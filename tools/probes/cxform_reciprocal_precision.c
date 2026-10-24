/* Independent arithmetic measurements, not a claim about Flash instructions. */
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
        volatile float unit = 1.0f / 255.0f;
        float divided = alpha / 255.0f;
        float multiplied = alpha * unit;
        printf("%d %08x %08x %08x %08x %08x\n", a,
               bits(estimate(alpha)), bits(divided), bits(estimate(divided)),
               bits(multiplied), bits(estimate(multiplied)));
    }
    return 0;
}
