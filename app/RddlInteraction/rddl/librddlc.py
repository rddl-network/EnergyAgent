import ctypes
import os
import sys
from ctypes import c_uint8, c_char_p, c_int, c_size_t, c_bool, POINTER, create_string_buffer
import platform

# Load the shared library
# system pick and optimistic architecture selection
if platform.system() == "Linux":
    if platform.processor() == "x86_64":
        lib_path = "app/lib/linux/x86_64/libRDDLC.so"
    elif os.uname().machine == "x86_64":  # linux-docker image has an empty platform.system() value
        lib_path = "app/lib/linux/x86_64/libRDDLC.so"
    else:
        lib_path = "app/lib/linux/armv7/libRDDLC.so"
else:
    sys.exit("unsupported OS, cannot load TA Wallet connector")

lib = ctypes.CDLL(lib_path)  # Adjust the path as needed

# Define constants
SEED_SIZE = 64
FROMHEX_MAXLEN = 256  # Adjust if needed
EXT_PUB_KEY_SIZE = 112  # Adjust if needed
PUB_KEY_SIZE = 33
ED25519_NAME = b"ed25519"
SECP256K1_NAME = b"secp256k1"

# Function: const char* getMnemonic()
lib.getMnemonic.restype = c_char_p
lib.getMnemonic.argtypes = []

# Function: void setRawSeed(char* seed64bytes)
lib.setRawSeed.restype = None
lib.setRawSeed.argtypes = [c_char_p]

# Function: void wipeSeed()
lib.wipeSeed.restype = None
lib.wipeSeed.argtypes = []

# Function: const char* setSeed(char* pMnemonic)
lib.setSeed.restype = c_char_p
lib.setSeed.argtypes = [c_char_p]

# Function: const char* getMnemonicFromSeed(const uint8_t* seed, size_t length)
lib.getMnemonicFromSeed.restype = c_char_p
lib.getMnemonicFromSeed.argtypes = [POINTER(c_uint8), c_size_t]

# Function: bool getSeedFromMnemonic(const char* pMnemonic, uint8_t* seedbuffer)
lib.getSeedFromMnemonic.restype = c_bool
lib.getSeedFromMnemonic.argtypes = [c_char_p, POINTER(c_uint8)]

# Function: bool getKeyFromSeed(const uint8_t* seed, uint8_t* priv_key, uint8_t* pub_key, const char* curve_name)
lib.getKeyFromSeed.restype = c_bool
lib.getKeyFromSeed.argtypes = [POINTER(c_uint8), POINTER(c_uint8), POINTER(c_uint8), c_char_p]

# Function: bool SignDataHash(const char* data_str, size_t data_length, char* pubkey_out, char* sig_out, char* hash_out)
lib.SignDataHash.restype = c_bool
lib.SignDataHash.argtypes = [c_char_p, c_size_t, c_char_p, c_char_p, c_char_p]

# Function: int SignDataHashWithPrivKey(const uint8_t* digest, const uint8_t* priv_key, char* sig_out)
lib.SignDataHashWithPrivKey.restype = c_int
lib.SignDataHashWithPrivKey.argtypes = [POINTER(c_uint8), POINTER(c_uint8), c_char_p]

# Function: bool verifyDataHash(const char* sig_str, const char* pub_key_str, const char* hash_str)
lib.verifyDataHash.restype = c_bool
lib.verifyDataHash.argtypes = [c_char_p, c_char_p, c_char_p]

# Function: bool getMachineIDSignature(uint8_t* priv_key, uint8_t* pub_key, uint8_t* signature, uint8_t* hash)
lib.getMachineIDSignature.restype = c_bool
lib.getMachineIDSignature.argtypes = [POINTER(c_uint8), POINTER(c_uint8), POINTER(c_uint8), POINTER(c_uint8)]

# Function: bool getMachineIDSignaturePublicKey(uint8_t* priv_key, uint8_t* pub_key, uint8_t* signature)
lib.getMachineIDSignaturePublicKey.restype = c_bool
lib.getMachineIDSignaturePublicKey.argtypes = [POINTER(c_uint8), POINTER(c_uint8), POINTER(c_uint8)]

# Function: const uint8_t* rddl_fromhex(const char* str)
lib.rddl_fromhex.restype = POINTER(c_uint8)
lib.rddl_fromhex.argtypes = [c_char_p]

# Function: size_t rddl_toHex(const uint8_t* array, size_t arraySize, char* output, size_t outputSize)
lib.rddl_toHex.restype = c_size_t
lib.rddl_toHex.argtypes = [POINTER(c_uint8), c_size_t, c_char_p, c_size_t]

# Function: const char* getRDDLAddress()
lib.getRDDLAddress.restype = c_char_p
lib.getRDDLAddress.argtypes = []

# Function: const char* getExtPubKeyLiquid()
lib.getExtPubKeyLiquid.restype = c_char_p
lib.getExtPubKeyLiquid.argtypes = []

# Function: const char* getExtPubKeyPlanetmint()
lib.getExtPubKeyPlanetmint.restype = c_char_p
lib.getExtPubKeyPlanetmint.argtypes = []

# Function: const char* getMachinePublicKeyHex()
lib.getMachinePublicKeyHex.restype = c_char_p
lib.getMachinePublicKeyHex.argtypes = []

# Function: const uint8_t* getPrivKeyLiquid()
lib.getPrivKeyLiquid.restype = POINTER(c_uint8)
lib.getPrivKeyLiquid.argtypes = []

# Function: const uint8_t* getPrivKeyPlanetmint()
lib.getPrivKeyPlanetmint.restype = POINTER(c_uint8)
lib.getPrivKeyPlanetmint.argtypes = []

# Function: const uint8_t* getPubKeyLiquid()
lib.getPubKeyLiquid.restype = POINTER(c_uint8)
lib.getPubKeyLiquid.argtypes = []

# Function: const uint8_t* getPubKeyPlanetmint()
lib.getPubKeyPlanetmint.restype = POINTER(c_uint8)
lib.getPubKeyPlanetmint.argtypes = []

# Function: const uint8_t* getMachinePublicKey()
lib.getMachinePublicKey.restype = POINTER(c_uint8)
lib.getMachinePublicKey.argtypes = []

# Function: bool getPlntmntKeys()
lib.getPlntmntKeys.restype = c_bool
lib.getPlntmntKeys.argtypes = []

# librddl functions


def get_mnemonic():
    return lib.getMnemonic().decode("utf-8")


def set_raw_seed(seed64bytes):
    lib.setRawSeed(seed64bytes.encode("utf-8"))


def wipe_seed():
    lib.wipeSeed()


def set_seed(mnemonic):
    return lib.setSeed(mnemonic.encode("utf-8")).decode("utf-8")


def get_mnemonic_from_seed(seed):
    return lib.getMnemonicFromSeed(seed, len(seed)).decode("utf-8")


def get_seed_from_mnemonic(mnemonic):
    seed_buffer = create_string_buffer(SEED_SIZE)
    result = lib.getSeedFromMnemonic(mnemonic.encode("utf-8"), seed_buffer)
    return result, seed_buffer.raw


def get_key_from_seed(seed, curve_name):
    priv_key = create_string_buffer(32)
    pub_key = create_string_buffer(33)
    result = lib.getKeyFromSeed(seed, priv_key, pub_key, curve_name.encode("utf-8"))
    return result, priv_key.raw, pub_key.raw


def sign_data_hash(data_str):
    pubkey_out = create_string_buffer(66)
    sig_out = create_string_buffer(128)
    hash_out = create_string_buffer(64)
    result = lib.SignDataHash(data_str.encode("utf-8"), len(data_str), pubkey_out, sig_out, hash_out)
    return result, pubkey_out.value.decode("utf-8"), sig_out.value.decode("utf-8"), hash_out.value.decode("utf-8")


def sign_data_hash_with_priv_key(digest, priv_key):
    sig_out = create_string_buffer(128)
    result = lib.SignDataHashWithPrivKey(digest, priv_key, sig_out)
    return result, sig_out.value.decode("utf-8")


def verify_data_hash(sig_str, pub_key_str, hash_str):
    return lib.verifyDataHash(sig_str.encode("utf-8"), pub_key_str.encode("utf-8"), hash_str.encode("utf-8"))


def rddl_fromhex(hex_str):
    result = lib.rddl_fromhex(hex_str.encode("utf-8"))
    return bytes(result[:FROMHEX_MAXLEN])


def rddl_toHex(byte_array):
    output = create_string_buffer(2 * len(byte_array))
    result = lib.rddl_toHex(byte_array, len(byte_array), output, len(output))
    return output.value.decode("utf-8")[:result]


# Pubkey functions


def get_rddl_address():
    return lib.getRDDLAddress().decode("utf-8")


def get_ext_pub_key_liquid():
    return lib.getExtPubKeyLiquid().decode("utf-8")


def get_ext_pub_key_planetmint():
    return lib.getExtPubKeyPlanetmint().decode("utf-8")


def get_machine_public_key_hex():
    return lib.getMachinePublicKeyHex().decode("utf-8")


def get_priv_key_liquid():
    return bytes(lib.getPrivKeyLiquid()[:32])


def get_priv_key_planetmint():
    return bytes(lib.getPrivKeyPlanetmint()[:32])


def get_pub_key_liquid():
    return bytes(lib.getPubKeyLiquid()[:PUB_KEY_SIZE])


def get_pub_key_planetmint():
    return bytes(lib.getPubKeyPlanetmint()[:PUB_KEY_SIZE])


def get_machine_public_key():
    return bytes(lib.getMachinePublicKey()[:PUB_KEY_SIZE])


def get_plntmnt_keys():
    return lib.getPlntmntKeys()
