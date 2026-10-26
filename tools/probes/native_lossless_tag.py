"""Emit explicit long headers for native lossless bitmap controls, including short payloads."""
import struct


def lossless2_tag(payload):
    if len(payload)<7:raise ValueError('Truncated lossless bitmap payload')
    return struct.pack('<HI',(36<<6)|63,len(payload))+payload
