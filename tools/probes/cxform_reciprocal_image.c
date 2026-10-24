/* Exhaust a fixed normalized-byte domain; never select from fitted bounds. */
#include <stdint.h>
#include <stdio.h>
#include <xmmintrin.h>

int main(void) {
    const uint32_t first=0x3b800000u, last=0x3f800000u;
    unsigned initial=_mm_getcsr();
    _mm_setcsr(initial & ~_MM_ROUND_MASK);
    printf("domain %08x %08x csr %08x\n",first,last,_mm_getcsr());
    uint32_t start=first, previous=0;
    unsigned long long count=0, rises=0;
    for(uint32_t input=first;input<=last;input+=4) {
        union { uint32_t u[4]; float f[4]; } source,result;
        for(unsigned j=0;j<4;j++) source.u[j]=input+j;
        _mm_storeu_ps(result.f,_mm_rcp_ps(_mm_loadu_ps(source.f)));
        for(unsigned j=0;j<4 && input+j<=last;j++) {
            uint32_t current=input+j, value=result.u[j];
            if(count && value!=previous) {
                printf("%08x %08x %08x\n",start,current-1,previous);
                start=current;
                if(value>previous) rises++;
            }
            previous=value;
            count++;
        }
    }
    printf("%08x %08x %08x\n",start,last,previous);
    printf("done %llu rises %llu\n",count,rises);
    _mm_setcsr(initial);
    return 0;
}
