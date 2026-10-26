import ctypes
import unittest
from types import SimpleNamespace
from tools.probes.read_owned_guest_memory import read_guest_entry


class Function:
    def __init__(self, function): self.function = function
    def __call__(self, *args): return self.function(*args)


class GuestMemoryTests(unittest.TestCase):
    def library(self, *, denied=False, short=False, raises=False):
        calls = []
        def task(own, pid, output):
            calls.append(('task',own,pid))
            ctypes.cast(output,ctypes.POINTER(ctypes.c_uint))[0] = 42
            return 5 if denied else 0
        def read(port,address,size,destination,actual):
            calls.append(('read',port,address,size))
            if raises: raise RuntimeError('read failed')
            ctypes.memmove(destination,b'0123456789abcdef',16)
            ctypes.cast(actual,ctypes.POINTER(ctypes.c_uint64))[0] = 15 if short else 16
            return 0
        def release(own,port):
            calls.append(('release',own,port));return 0
        return SimpleNamespace(own_task=7,task_for_pid=Function(task),
            mach_vm_read_overwrite=Function(read),mach_port_deallocate=Function(release)),calls

    def test_independent_exact_read_and_release(self):
        library,calls=self.library()
        result=read_guest_entry(123,0x1000,library=library)
        self.assertTrue(result['guest_virtual_read_verified'])
        self.assertFalse(result['physical_memory_verified'])
        self.assertFalse(result['rosetta_translated_instructions_verified'])
        self.assertEqual(result['bytes_hex'],b'0123456789abcdef'.hex())
        self.assertEqual(calls,[('task',7,123),('read',42,0x1000,16),('release',7,42)])

    def test_denial_and_partial_reads_fail_closed(self):
        for denied,short in ((True,False),(False,True)):
            library,calls=self.library(denied=denied,short=short)
            result=read_guest_entry(123,0x1000,library=library)
            self.assertFalse(result['guest_virtual_read_verified'])
            self.assertNotIn('bytes_hex',result)
            self.assertEqual(len(calls),1 if denied else 3)

    def test_read_exception_releases_task_right(self):
        library,calls=self.library(raises=True)
        with self.assertRaises(RuntimeError): read_guest_entry(123,0x1000,library=library)
        self.assertEqual(calls[-1],('release',7,42))

    def test_invalid_input_does_not_load_library(self):
        for pid,address in ((0,0x1000),(2**31,0x1000),(2**32+123,0x1000),(True,0x1000),(1,True),(1,-1),(1,2**64)):
            with self.assertRaises(ValueError): read_guest_entry(pid,address,library=object())
