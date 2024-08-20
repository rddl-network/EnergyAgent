import ctypes
from ctypes import c_int, c_uint8, c_size_t, POINTER, byref, create_string_buffer
import threading

from app.RddlInteraction.TrustWallet.ITrustWalletConnector import ITrustWalletConnector
from app.helpers.models import PlanetMintKeys
from app.helpers.logs import logger, log


class TrustWalletConnectorATECC608(ITrustWalletConnector):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TrustWalletConnectorATECC608, cls).__new__(cls)
            cls._instance.__init__(*args, **kwargs)
        return cls._instance

    def __init__(self):
        self.atecc608_lib = ctypes.CDLL("../build/libatecc608_handler.so")
        self._init_atecc608_functions()
        self.plmnt_keys = None

    def _init_atecc608_functions(self):
        # Initialize function signatures
        self.atecc608_lib.atecc_handler_init.argtypes = [c_int, c_int]
        self.atecc608_lib.atecc_handler_init.restype = c_int
        self.atecc608_lib.atecc_handler_genkey.argtypes = [c_int, POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_genkey.restype = c_int
        self.atecc608_lib.atecc_handler_get_public_key.argtypes = [c_int, POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_get_public_key.restype = c_int
        self.atecc608_lib.atecc_handler_sign.argtypes = [c_int, POINTER(c_uint8), POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_sign.restype = c_int
        self.atecc608_lib.atecc_handler_verify.argtypes = [c_int, POINTER(c_uint8), POINTER(c_uint8), POINTER(c_uint8)]
        self.atecc608_lib.atecc_handler_verify.restype = c_int

        # Initialize the ATECC608
        status = self.atecc608_lib.atecc_handler_init(0xC0, 1)
        if status:
            raise RuntimeError(f"Failed to initialize ATECC608: {status}")

    @log
    def create_keypair_nist(self, ctx: int) -> str:
        with self._lock:
            pub_key = (c_uint8 * 64)()
            status = self.atecc608_lib.atecc_handler_genkey(ctx, pub_key)
            if status:
                raise RuntimeError(f"Failed to generate key: {status}")
            return bytes(pub_key).hex()

    @log
    def get_machine_id(self, ctx: int) -> str:
        with self._lock:
            pub_key = (c_uint8 * 64)()
            status = self.atecc608_lib.atecc_handler_get_public_key(ctx, pub_key)
            if status:
                raise RuntimeError(f"Failed to get public key: {status}")
            return bytes(pub_key).hex()

    @log
    def sign_with_nist(self, data_to_sign: str, ctx: int) -> str:
        with self._lock:
            msg = (c_uint8 * 32)(*bytes.fromhex(data_to_sign))
            signature = (c_uint8 * 64)()
            status = self.atecc608_lib.atecc_handler_sign(ctx, msg, signature)
            if status:
                raise RuntimeError(f"Failed to sign data: {status}")
            return bytes(signature).hex()

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
    def create_mnemonic(self) -> str:
        # Implement mnemonic creation logic
        pass

    @log
    def recover_from_mnemonic(self, mnemonic: str) -> str:
        # Implement mnemonic recovery logic
        pass

    @log
    def get_planetmint_keys(self) -> PlanetMintKeys:
        # Implement logic to get PlanetMint keys
        pass

    @log
    def get_seed_secp256k1(self):
        # Implement logic to get secp256k1 seed
        pass

    @log
    def sign_hash_with_planetmint(self, data_to_sign: str) -> str:
        # Implement PlanetMint signing logic
        pass

    @log
    def sign_hash_with_rddl(self, data_to_sign: str) -> str:
        # Implement RDDL signing logic
        pass
