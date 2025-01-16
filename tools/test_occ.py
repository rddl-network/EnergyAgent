from osc4py3.oscbuildparse import *

import ctypes

# Load the shared library
occ = ctypes.CDLL("./libocc.so")

# Define the Zig function prototype
# Assuming your Zig function now looks like this:
# export fn occ_do(data: [*]const u8, length: usize, outBuffer: [*]u8, outBufferSize: usize) usize;
occ.occ_do.argtypes = [
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.c_size_t,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_ubyte),
    ctypes.c_size_t,
]
occ.occ_do.restype = ctypes.c_size_t

# Prepare the occ messages.

# msg = OSCMessage('/IHW/bip39Mnemonic', ',is', [0, ""])
msg = OSCMessage("/IHW/mnemonicToSeed", ",", [""])

portName = "/dev/ttyACM0"
portNameBytes = bytearray(portName, "utf-8")

port_name_ptr = (ctypes.c_ubyte * len(portNameBytes))(*portNameBytes)
input_data = encode_packet(msg)
print(input_data)

input_ptr = (ctypes.c_ubyte * len(input_data))(*input_data)

# Prepare the output buffer
output_buffer_size = 1024  # Choose an appropriate size
output_buffer = (ctypes.c_ubyte * output_buffer_size)()
buffer_delay_ms = 200  # reading from input buffer delay in ms
# Call the function

output_length = occ.occ_do(
    input_ptr, len(input_data), output_buffer, output_buffer_size, buffer_delay_ms, port_name_ptr, len(portNameBytes)
)

# Access the returned data
returned_data = bytes(output_buffer[:output_length])
print("Returned Data:", returned_data)
