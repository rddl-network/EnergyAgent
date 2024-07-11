import ctypes
import os

from osc4py3.oscbuildparse import encode_packet
from app.helpers.models import OSCResponse


def load_occ_library(lib_path):
    lib_occ = ctypes.CDLL(lib_path)
    lib_occ.occ_do.argtypes = [
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_size_t,
    ]
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

    def prepare_buffer(self, encoded_packet):
        input_ptr = (ctypes.c_ubyte * len(encoded_packet))(*encoded_packet)
        output_buffer = (ctypes.c_ubyte * self.buffer_size)()
        return input_ptr, output_buffer

    def call_occ_do(self, input_ptr, len_input_data, output_buffer):
        return self.lib_occ.occ_do(
            input_ptr,
            len_input_data,
            output_buffer,
            self.buffer_size,
            self.buffer_delay_ms,
            self.port_name_ptr,
            len(self.port_name_ptr),
        )

    def send_message(self, message) -> OSCResponse:
        encoded_data = encode_packet(message)
        input_ptr, output_buffer = self.prepare_buffer(encoded_data)
        output_length = self.call_occ_do(input_ptr, len(encoded_data), output_buffer)
        returned_data = bytes(output_buffer[:output_length])
        return extract_information(returned_data)


def extract_information(response_bytes):
    try:
        # Decode the byte string, assuming UTF-8 encoding.
        decoded_string = response_bytes.decode("utf-8")

        # Split the string on null characters to clean and separate the data.
        parts = decoded_string.split("\x00")

        # Filter out any empty strings that may result from consecutive nulls or trailing nulls
        parts = [part.strip() for part in parts if part.strip()]

        if parts:
            # The first part before the first comma is assumed to be the command
            # and the rest are data values.
            command_part = parts[0]
            data_parts = parts[1:]  # The rest are considered data parts

            if "," in command_part:
                command, first_data = command_part.split(",", 1)
                # Prepend the first data part split from command to the rest of the data parts
                data_parts = [first_data] + data_parts
            else:
                command = command_part
                # If no comma was found, all other parts are data parts

            return OSCResponse(command=command.strip(), data=[data.strip() for data in data_parts])
        else:
            return OSCResponse(data=["No valid data found."])

    except UnicodeDecodeError as e:
        # Return an empty OSCResponse with an error in data field if there is a decoding error.
        return OSCResponse(data=[f"Error decoding the response: {str(e)}"])


def is_not_connected(wallet_port):
    return not os.path.exists(wallet_port)
