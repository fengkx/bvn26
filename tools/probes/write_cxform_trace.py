"""Write an optional native-path debugger script; never launch it implicitly."""
import argparse
import json
from pathlib import Path


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--movie',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    callback = Path(__file__).with_name('cxform_trace_callback.py').resolve()
    quote = lambda p:json.dumps(str(p.resolve()))
    lines = ['settings set target.disable-aslr false',f'target create --arch x86_64 {quote(args.binary)}',
             f'settings set target.run-args {quote(args.movie)}',f'command script import {quote(callback)}',
             'breakpoint set --address 0x1001fc529','breakpoint command add -F cxform_trace_callback.stop 1','run',
             'register read --format float xmm0 xmm1 xmm2 xmm4 xmm5 xmm6 xmm7 xmm8 xmm12 xmm13 xmm14 xmm15',
             'register read rip rbp rdi rsi rdx rcx mxcsr','bt 8','process kill']
    args.output.write_text('\n'.join(lines)+'\n')
