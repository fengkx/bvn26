/* Fixed instruction experiments, not an inference about Flash's implementation. */
#include <stdio.h>
#include <xmmintrin.h>

static __m128 number(int n) { return _mm_cvtsi32_ss(_mm_setzero_ps(), n); }
static __m128 mul(__m128 a, __m128 b) { return _mm_mul_ss(a,b); }
static __m128 divv(__m128 a, __m128 b) { return _mm_div_ss(a,b); }
static int evaluate(int c, int a, int m, int d, int op, int form) {
    __m128 source=number(c), alpha=number(a), denominator=number(255);
    __m128 reciprocal;
    if(form==0) reciprocal=_mm_rcp_ss(alpha);
    else {
        if(form==1) {
            source=divv(source,denominator);
            alpha=divv(alpha,denominator);
        } else {
            __m128 normalizer=divv(number(1),denominator);
            source=mul(source,normalizer);
            alpha=mul(alpha,normalizer);
        }
        reciprocal=_mm_rcp_ss(alpha);
    }
    __m128 straight=mul(source,reciprocal);
    __m128 value=_mm_add_ss(mul(straight,divv(number(m),number(256))),divv(number(d),denominator));
    value=_mm_max_ss(_mm_setzero_ps(),_mm_min_ss(number(1),value));
    value=mul(mul(value,number(a)),divv(number(op*256/100),number(256)));
    return _mm_cvttss_si32(value);
}

int main(void) {
    unsigned initial=_mm_getcsr();
    const unsigned modes[]={_MM_ROUND_NEAREST,_MM_ROUND_DOWN,_MM_ROUND_UP,_MM_ROUND_TOWARD_ZERO};
    int c,a,m,d,op,id=0;
    printf("initial %08x\n",initial);
    while(scanf("%d %d %d %d %d",&c,&a,&m,&d,&op)==5) {
        printf("%d",id++);
        for(int mode=0;mode<4;mode++) {
            _mm_setcsr((initial & ~_MM_ROUND_MASK)|modes[mode]);
            printf(" %04x",_mm_getcsr() & _MM_ROUND_MASK);
            for(int form=0;form<3;form++) printf(" %d",evaluate(c,a,m,d,op,form));
        }
        puts("");
    }
    _mm_setcsr(initial);
    return ferror(stdin)?1:0;
}
