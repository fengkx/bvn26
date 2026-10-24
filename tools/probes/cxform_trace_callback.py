"""Optional LLDB read-only stop predicate; not evidence until a breakpoint hits."""
import struct
import lldb


def stop(frame, location, internal):
    error = lldb.SBError()
    raw = frame.FindRegister('xmm2').GetData().ReadRawData(error,0,16)
    if not error.Success() or struct.unpack('<4f',raw)!=(49.0,)*4:
        return False
    print('NATIVE_ALPHA49_SITE_HIT')
    return True
