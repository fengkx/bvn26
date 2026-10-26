#include <xmmintrin.h>
#include <stdint.h>
#include <stdio.h>
int main(void) {
    for(int a=1;a<256;a++) {
        union { float f; uint32_t u; } value;
        value.f = _mm_cvtss_f32(_mm_rcp_ps(_mm_set1_ps((float)a)));
        printf("%d %08x\n",a,value.u);
    }
    return 0;
}
