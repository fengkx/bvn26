/* Fixed post-scaling constructions and domains; no native constraints are read. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <xmmintrin.h>

int main(int argc, char **argv) {
    if(argc!=2 || argv[1][1] || argv[1][0]<'0' || argv[1][0]>'3') return 2;
    unsigned form=(unsigned)(argv[1][0]-'0');
    const uint32_t firsts[]={0x3f800000u,0x437f0000u,0x3b800000u,0x3b800000u};
    const uint32_t lasts[]={0x437f0000u,0x477e0100u,0x3f800000u,0x3f800000u};
    uint32_t first=firsts[form],last=lasts[form];
    unsigned initial=_mm_getcsr();
    _mm_setcsr(initial & ~_MM_ROUND_MASK);
    __m128 scale=_mm_set1_ps(255.0f), normalizer=_mm_rcp_ps(scale);
    printf("form %u domain %08x %08x csr %08x\n",form,first,last,_mm_getcsr());
    uint32_t start=first,previous=0;
    unsigned long long count=0,rises=0;
    for(uint32_t input=first;input<=last;input+=4) {
        union { uint32_t u[4]; float f[4]; } source,result;
        for(unsigned j=0;j<4;j++) source.u[j]=input+j;
        __m128 value=_mm_rcp_ps(_mm_loadu_ps(source.f));
        if(form==1) value=_mm_mul_ps(value,scale);
        if(form==2) value=_mm_div_ps(value,scale);
        if(form==3) value=_mm_mul_ps(value,normalizer);
        value=_mm_mul_ps(value,scale);
        _mm_storeu_ps(result.f,value);
        for(unsigned j=0;j<4 && input+j<=last;j++) {
            uint32_t current=input+j,value_bits=result.u[j];
            if(count && value_bits!=previous) {
                printf("%08x %08x %08x\n",start,current-1,previous);
                start=current;
                if(value_bits>previous) rises++;
            }
            previous=value_bits;
            count++;
        }
    }
    printf("%08x %08x %08x\n",start,last,previous);
    printf("done %llu rises %llu\n",count,rises);
    _mm_setcsr(initial);
    return 0;
}
