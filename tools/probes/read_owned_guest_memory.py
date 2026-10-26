"""Read a bounded guest virtual entry prefix through Mach, independently of LLDB."""


def read_guest_entry(pid, address, *, library=None):
    import ctypes

    if type(pid) is not int or not 0 < pid < 2**31 or type(address) is not int or not 0 < address < 2**64-16:
        raise ValueError('Invalid owned PID or guest virtual address')
    system = library if library is not None else ctypes.CDLL('/usr/lib/libSystem.B.dylib')
    system.task_for_pid.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]
    system.task_for_pid.restype = ctypes.c_int
    system.mach_vm_read_overwrite.argtypes = [ctypes.c_uint, ctypes.c_uint64, ctypes.c_uint64,
                                            ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
    system.mach_vm_read_overwrite.restype = ctypes.c_int
    system.mach_port_deallocate.argtypes = [ctypes.c_uint, ctypes.c_uint]
    system.mach_port_deallocate.restype = ctypes.c_int
    own_task = (ctypes.c_uint.in_dll(system, 'mach_task_self_').value
                if library is None else system.own_task)
    task = ctypes.c_uint()
    result = {'pid': pid, 'guest_virtual_address': hex(address), 'requested_bytes': 16,
              'guest_virtual_read_verified': False, 'physical_memory_verified': False,
              'rosetta_translated_instructions_verified': False}
    code = system.task_for_pid(own_task, pid, ctypes.byref(task))
    result['task_for_pid_return'] = code
    if code != 0:
        return result
    try:
        if not task.value:
            raise RuntimeError('Successful task_for_pid returned null task port')
        buffer = ctypes.create_string_buffer(16)
        actual = ctypes.c_uint64()
        code = system.mach_vm_read_overwrite(task.value, address, 16, ctypes.addressof(buffer), ctypes.byref(actual))
        result['mach_vm_read_overwrite_return'] = code
        result['actual_bytes'] = actual.value
        if code == 0 and actual.value == 16:
            result['bytes_hex'] = buffer.raw.hex()
            result['guest_virtual_read_verified'] = True
    finally:
        if task.value:
            result['mach_port_deallocate_return'] = system.mach_port_deallocate(own_task, task.value)
    return result
