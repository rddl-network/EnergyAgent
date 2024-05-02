import ctypes
from osc4py3.oscbuildparse import *


def load_occ_library(lib_path):
    lib_occ = ctypes.CDLL(lib_path)
    lib_occ.occ_do.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t,
                               ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t,
                               ctypes.c_size_t, ctypes.POINTER(ctypes.c_ubyte),
                               ctypes.c_size_t]
    lib_occ.occ_do.restype = ctypes.c_size_t
    return lib_occ


def prepare_port(port_name):
    port_name_bytes = bytearray(port_name, "utf-8")
    port_name_ptr = (ctypes.c_ubyte * len(port_name_bytes))(*port_name_bytes)
    return port_name_ptr


class OSCMessageSender:
    def __init__(self, lib_path, port_name, buffer_size=1024, buffer_delay_ms=200):
        self.lib_occ = load_occ_library(lib_path)
        self.buffer_size = buffer_size
        self.buffer_delay_ms = buffer_delay_ms
        self.port_name_ptr = prepare_port(port_name)

    def prepare_buffer(self, message):
        input_data = encode_packet(message)
        input_ptr = (ctypes.c_ubyte * len(input_data))(*input_data)
        output_buffer = (ctypes.c_ubyte * self.buffer_size)()
        return input_ptr, output_buffer

    def call_occ_do(self, input_ptr, len_input_data, output_buffer):
        return self.lib_occ.occ_do(input_ptr, len_input_data, output_buffer, self.buffer_size,
                                   self.buffer_delay_ms, self.port_name_ptr, len(self.port_name_ptr))

    def send_message(self, message):
        input_ptr, output_buffer = self.prepare_buffer(message)
        output_length = self.call_occ_do(input_ptr, len(message), output_buffer)
        returned_data = bytes(output_buffer[:output_length])
        return returned_data
