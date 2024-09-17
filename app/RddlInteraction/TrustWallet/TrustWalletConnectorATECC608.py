import ctypes
import os
import sys
from abc import ABC
from ctypes import c_int, c_uint8, c_size_t, POINTER
import threading
import platform

from bip_utils import Bip39SeedGenerator
from mnemonic import Mnemonic
from ecdsa import SigningKey, SECP256k1

from app.RddlInteraction.TrustWallet.ITrustWalletConnector import ITrustWalletConnector
from app.RddlInteraction.rddl.librddlc import (
    set_raw_seed,
    get_priv_key_planetmint,
    wipe_seed,
    get_priv_key_liquid,
    get_rddl_address,
    get_pub_key_planetmint,
    get_pub_key_liquid,
)
from app.helpers.models import PlanetMintKeys
from app.helpers.logs import log

I2C_ADDR = 0xC0
PLANETMINT_SLOT = 3
PRE_ATTEST_SLOT = 2


class TrustWalletConnectorATECC608(ITrustWalletConnector, ABC):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TrustWalletConnectorATECC608, cls).__new__(cls)
            cls._instance.__init__(*args, **kwargs)
        return cls._instance

    def __init__(self):
        if platform.system() == "Linux":
            if platform.processor() == "x86_64":
                lib_path = "app/lib/linux/x86_64/libatecc608_handler.so"
            elif os.uname().machine == "x86_64":  # linux-docker image has an empty platform.system() value
                lib_path = "app/lib/linux/x86_64/libatecc608_handler.so"
            else:
                lib_path = "app/lib/linux/armv7/libatecc608_handler.so"
        else:
            sys.exit("unsupported OS, cannot load TA Wallet connector")
        self.atecc608_lib = ctypes.CDLL(lib_path)
        self._init_atecc608_functions()
        self.plmnt_keys = None

    def _init_atecc608_functions(self):
        # Initialize function signatures
        self.atecc608_lib.atecc_handler_init.argtypes = [c_int, c_int]
        self.atecc608_lib.atecc_handler_init.restype = c_int
        self.atecc608_lib.atecc_handler_write_configuration.argtypes = [POINTER(c_uint8), c_size_t]
        self.atecc608_lib.atecc_handler_write_configuration.restype = c_int
        self.atecc608_lib.atecc_handle_write_default_configuration.restype = c_int
        self.atecc608_lib.atecc_handler_lock_zone.argtypes = [c_uint8]
        self.atecc608_lib.atecc_handler_lock_zone.restype = c_int
        self.atecc608_lib.atecc_handler_inject_priv_key.argtypes = [c_int, POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_inject_priv_key.restype = c_int
        self.atecc608_lib.atecc_handler_genkey.argtypes = [c_int, POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_genkey.restype = c_int
        self.atecc608_lib.atecc_handler_get_public_key.argtypes = [c_int, POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_get_public_key.restype = c_int
        self.atecc608_lib.atecc_handler_sign.argtypes = [c_int, POINTER(c_uint8), POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_sign.restype = c_int
        self.atecc608_lib.atecc_handler_verify.argtypes = [c_int, POINTER(c_uint8), POINTER(c_uint8), POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_verify.restype = c_int
        self.atecc608_lib.atecc_handler_write_data.argtypes = [c_int, POINTER(c_uint8), c_size_t]
        self.atecc608_lib.atecc_handler_write_data.restype = c_int
        self.atecc608_lib.atecc_handler_read_data.argtypes = [c_int, POINTER(c_uint8), c_size_t]
        self.atecc608_lib.atecc_handler_read_data.restype = c_int

        # Initialize the ATECC608
        status = self.atecc608_lib.atecc_handler_init(I2C_ADDR, 1)
        if status:
            raise RuntimeError(f"Failed to initialize ATECC608: {status}")

    @log
    def write_atecc_config(self):
        with self._lock:
            status = self.atecc608_lib.atecc_handler_init(I2C_ADDR, 1)
            if status:
                raise RuntimeError(f"Failed to initialize ATECC608: {status}")

            status = self.atecc608_lib.atecc_handle_write_default_configuration()
            if status:
                raise RuntimeError(f"Failed to write configuration: {status}")

            status = self.atecc608_lib.atecc_handler_lock_zone(0)
            if status:
                raise RuntimeError(f"Failed to lock zone: {status}")

    @log
    def inject_priv_key(self, priv_key: bytes):
        with self._lock:
            status = self.atecc608_lib.atecc_handler_inject_priv_key(PRE_ATTEST_SLOT, priv_key)
            if status:
                raise RuntimeError(f"Failed to inject private key: {status}")

    @log
    def create_keypair_nist(self, ctx: int) -> str:
        with self._lock:
            pub_key = (c_uint8 * 64)()
            status = self.atecc608_lib.atecc_handler_genkey(ctx, pub_key)
            if status:
                raise RuntimeError(f"Failed to generate key: {status}")
            return print_hex_buffer(pub_key)

    @log
    def get_machine_id(self, ctx: int) -> str:
        with self._lock:
            pub_key = (c_uint8 * 64)()
            status = self.atecc608_lib.atecc_handler_get_public_key(ctx, pub_key)
            if status:
                raise RuntimeError(f"Failed to get public key: {status}")
            return print_hex_buffer(pub_key)

    @log
    def sign_with_nist(self, data_to_sign: str, ctx: int) -> str:
        with self._lock:
            msg = (c_uint8 * 32)(*bytes.fromhex(data_to_sign))
            signature = (c_uint8 * 64)()
            status = self.atecc608_lib.atecc_handler_sign(ctx, msg, signature)
            if status:
                raise RuntimeError(f"Failed to sign data: {status}")
            return print_hex_buffer(signature)

    @log
    def verify_nist_signature(self, data_to_sign: str, signature: str, ctx: int) -> bool:
        with self._lock:
            msg = (c_uint8 * 32)(*bytes.fromhex(data_to_sign))
            sig = (c_uint8 * 64)(*bytes.fromhex(signature))
            pub_key = (c_uint8 * 64)()
            self.atecc608_lib.atecc_handler_get_public_key(ctx, pub_key)
            status = self.atecc608_lib.atecc_handler_verify(ctx, msg, sig, pub_key)
            return status == 0

    # Implement other methods from ITrustWalletConnector...

    @log
    def create_mnemonic(self):
        with self._lock:
            mnemo = Mnemonic("english")
            mnemonic = mnemo.generate(strength=256)  # 24 words
            seed = Bip39SeedGenerator(mnemonic).Generate()
            status = self.atecc608_lib.atecc_handler_write_data(PLANETMINT_SLOT, seed, len(seed))
            if status:
                raise RuntimeError(f"Failed to store seed: {status}")
            return mnemonic, seed

    @log
    def recover_from_mnemonic(self, mnemonic: str) -> str:
        with self._lock:
            seed = Bip39SeedGenerator(mnemonic).Generate()
            status = self.atecc608_lib.atecc_handler_write_data(PLANETMINT_SLOT, seed, len(seed))
            if status:
                raise RuntimeError(f"Failed to store seed: {status}")
            return seed.hex()

    @log
    def get_planetmint_keys(self) -> PlanetMintKeys:
        with self._lock:
            seed = (c_uint8 * 64)()
            status = self.atecc608_lib.atecc_handler_read_data(0xC2, seed, 64)
            if status:
                raise RuntimeError(f"Failed to get public key: {status}")
            planet_mint_keys = PlanetMintKeys()
            set_raw_seed(seed)
            planet_mint_keys.planetmint_address = get_rddl_address()
            planet_mint_keys.extended_planetmint_pubkey = get_pub_key_planetmint()
            planet_mint_keys.extended_liquid_pubkey = get_pub_key_liquid()
            wipe_seed()
            return planet_mint_keys

    @log
    def sign_hash_with_planetmint(self, data_to_sign: str) -> str:
        with self._lock:
            seed = (c_uint8 * 64)()
            status = self.atecc608_lib.atecc_handler_read_data(PLANETMINT_SLOT, seed, 64)
            if status:
                raise RuntimeError(f"Failed to get public key: {status}")
            set_raw_seed(seed)
            priv_key = get_priv_key_planetmint()
            signing_key = SigningKey.from_string(priv_key, curve=SECP256k1)
            signature = signing_key.sign_deterministic(data_to_sign.encode())
            wipe_seed()
            return bytes(signature).hex()

    @log
    def sign_hash_with_rddl(self, data_to_sign: str) -> str:
        with self._lock:
            seed = (c_uint8 * 64)()  # type: ignore # mypy bug  # https
            status = self.atecc608_lib.atecc_handler_read_data(PLANETMINT_SLOT, seed, 64)
            if status:
                raise RuntimeError(f"Failed to get public key: {status}")
            set_raw_seed(seed)
            priv_key = get_priv_key_liquid()
            signing_key = SigningKey.from_string(priv_key, curve=SECP256k1)
            signature = signing_key.sign_deterministic(data_to_sign.encode())
            wipe_seed()
            return bytes(signature).hex()


def print_hex_buffer(input):
    return "".join([f"{x:02x}" for x in input])
