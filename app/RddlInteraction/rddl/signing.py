import hashlib

from ecdsa import SigningKey, SECP256k1
from ecdsa.util import sigencode_string_canonize

from ripemd.ripemd160 import ripemd160
from bitcoinaddress import segwit_addr


def base32_5to8(in_data: bytes) -> bytes:
    """Converts a base32 encoded byte array (5 bits per byte) to base64 (8 bits per byte).

    **WARNING**: This function replicates the original C code's logic for easier comparison
    but might not be as efficient as a loop-based approach.

    Args:
        in_data: A byte array containing the base32 encoded data.
        out_data: An empty byte array with a length at least (len(in_data) * 8) // 5.

    Returns:
        A new byte array containing the decoded data with a size equal to the number of
        written bytes (depends on the input length).
    """
    length = len(in_data)
    written_bytes = 0
    out_data = bytearray(8)
    if length >= 1:
        out_data[0] = in_data[0] >> 3
        written_bytes = 1
        if length >= 2:
            out_data[1] = (in_data[0] & 7) << 2
            written_bytes = 2

    if length >= 2:
        out_data[1] |= in_data[1] >> 6
        written_bytes = max(written_bytes, 2)
        if length >= 3:
            out_data[2] = (in_data[1] >> 1) & 31
            out_data[3] = (in_data[1] & 1) << 4
            written_bytes = max(written_bytes, 4)

    if length >= 3:
        out_data[3] |= in_data[2] >> 4
        written_bytes = max(written_bytes, 4)
        if length >= 4:
            out_data[4] = (in_data[2] & 15) << 1
            written_bytes = max(written_bytes, 5)

    if length >= 4:
        out_data[4] |= in_data[3] >> 7
        written_bytes = max(written_bytes, 5)
        if length >= 5:
            out_data[5] = (in_data[3] >> 2) & 31
            out_data[6] = (in_data[3] & 3) << 3
            written_bytes = max(written_bytes, 7)

    if length >= 5:
        out_data[6] |= in_data[4] >> 5
        written_bytes = max(written_bytes, 8)
        out_data[7] = in_data[4] & 31

    # Create a new byte array with the actual written data size
    return out_data[:written_bytes]


def base32_encode_unsafe(in_data: bytes):
    """Encodes a byte array (unsafe, no padding) in base32 to base64.

    **WARNING**: This function performs unsafe base32 to base64 conversion without
    padding. Ensure your input length is a multiple of 5 for proper decoding.

    Args:
        in_data: A byte array containing the data to encode.
        out_data: An empty byte array with a length at least (len(in_data) * 8) // 5 to store the encoded data.
    """
    out_data = b""
    in_length = len(in_data)
    remainder = in_length % 5

    # Calculate the number of full 5-bit blocks
    full_blocks = in_length - remainder

    # Process full blocks using the existing function
    for i in range(0, full_blocks, 5):
        b32Bytes = base32_5to8(in_data[i : i + 5])
        out_data = out_data + b32Bytes

    # Process remaining bytes (if any)
    if remainder:
        b32Bytes = base32_5to8(in_data[full_blocks:])
        out_data = out_data + b32Bytes
    return out_data


def ripemd(v):
    r = hashlib.new("ripemd160")
    r.update(v)
    return r


def hash160(v):
    sah256Hash = getHash(v)
    return ripemd(sah256Hash)


def getAddressStringFromAddressBytes(address: bytes):
    hrp = "plmnt"
    base23EncData = base32_encode_unsafe(bytes(address))
    base23ByteList = [byte for byte in base23EncData]
    bech32AddressString = segwit_addr.bech32_encode(hrp, base23ByteList)
    return bech32AddressString


def getAddressStringFromPubKey(public_key: bytes):
    addressBytes = pubkey2address(public_key)
    return getAddressStringFromAddressBytes(addressBytes)


def pubkey2address(pubkey: bytes) -> bytes:
    sha256hash = getHash(pubkey)
    ripemdhash = ripemd160(sha256hash)
    return ripemdhash


def addressBytes2StringNew(address: bytes) -> str:
    hrp = "plmnt"
    b32Address = base32_encode_unsafe(address)
    bech32AddressString = segwit_addr.bech32_encode(hrp, b32Address)

    return bech32AddressString


def addressBytes2String(address: bytes) -> str:
    hrp = "plmnt"
    b32Address = base32.b32encode(address, split_every=0, checksum=True)
    byte_list = [b for b in b32Address]
    byte_list = [char(b) for b in b32Address]
    bech32AddressString = segwit_addr.bech32_encode(hrp, byte_list)
    return bech32AddressString


def getHash(data: bytes) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(data)
    digest = hasher.digest()
    return digest


def signBytesWithKey(data: bytes, private_key: bytes) -> bytes:
    # Decode the signing key bytes
    signing_key = SigningKey.from_string(private_key, curve=SECP256k1, hashfunc=hashlib.sha256)

    # Sign the message with the private key
    signature = signing_key.sign_deterministic(data, hashfunc=hashlib.sha256, sigencode=sigencode_string_canonize)
    return signature
