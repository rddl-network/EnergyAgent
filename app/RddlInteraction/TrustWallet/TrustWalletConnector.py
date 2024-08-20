import os
import sys
import platform
import threading
from osc4py3.oscbuildparse import OSCMessage

from app.RddlInteraction.TrustWallet.ITrustWalletConnector import ITrustWalletConnector
from app.RddlInteraction.TrustWallet.osc_message_sender import OSCMessageSender
from app.helpers.models import PlanetMintKeys
from app.helpers.logs import logger, log

PREFIX_IHW = "/IHW"


class TrustWalletConnector(ITrustWalletConnector):
    _instance = None
    occ_message_sender = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        print("TrustWallet Demand")
        if not getattr(cls, "_instance", None):
            cls._instance = super().__new__(cls)
            cls._instance.__init__(*args, **kwargs)  # Call __init__ manually
        return cls._instance

    def __init__(self, port_name):
        # system pick and optimistic architecture selection
        if platform.system() == "Linux":
            if platform.processor() == "x86_64":
                lib_path = "app/lib/linux/x86_64/libocc.so"
            elif os.uname().machine == "x86_64":  # linux-docker image has an empty platform.system() value
                lib_path = "app/lib/linux/x86_64/libocc.so"
            else:
                lib_path = "app/lib/linux/armv7/libocc.so"
        elif platform.system() == "Darwin":
            lib_path = "app/lib/macos/aarch/libpyocc.dylib"
        else:
            sys.exit("unsupported OS, cannot load TA Wallet connector")

        if self.occ_message_sender is None and len(port_name) > 0:
            print("New OSC Message Connector: " + port_name)
            self.occ_message_sender = OSCMessageSender(lib_path, port_name)
        self.plmnt_keys = None

    @log
    def create_mnemonic(self):
        with self._lock:
            """
            @brief: Derives the private key from the mnemonic seed
            """
            msg = OSCMessage(f"{PREFIX_IHW}/mnemonicToSeed", ",i", [1])
            occ_message = self.occ_message_sender.send_message(msg)
            print(occ_message)
            self.plmnt_keys = None
            return occ_message.data[1]

    @log
    def recover_from_mnemonic(self, mnemonic: str) -> str:
        with self._lock:
            """
            @brief: Derives the private key from the mnemonic seed
            """
            msg = OSCMessage(f"{PREFIX_IHW}/mnemonicToSeed", ",is", [1, mnemonic])
            occ_message = self.occ_message_sender.send_message(msg)
            self.plmnt_keys = None
            return occ_message.data[1]

    @log
    def get_planetmint_keys(self) -> PlanetMintKeys:
        with self._lock:
            """
            @brief: Gets the seed
            @return: return seed
            """
            if self.plmnt_keys is None:
                print("Send key query OSC Message")
                msg = OSCMessage(f"{PREFIX_IHW}/getPlntmntKeys", ",", [])
                occ_message = self.occ_message_sender.send_message(msg)
                self.plmnt_keys = PlanetMintKeys()
                if len(occ_message.data) < 5:
                    logger.error("Trust Wallet not initialized. Please initialize the wallet.")
                    return self.plmnt_keys
                self.plmnt_keys.planetmint_address = occ_message.data[1]
                self.plmnt_keys.extended_liquid_pubkey = occ_message.data[2]
                self.plmnt_keys.extended_planetmint_pubkey = occ_message.data[3]
                self.plmnt_keys.raw_planetmint_pubkey = occ_message.data[4]
            return self.plmnt_keys

    @log
    def get_seed_secp256k1(self):
        with self._lock:
            msg = OSCMessage(f"{PREFIX_IHW}/se050GetSeed", ",", [])
            occ_message = self.occ_message_sender.send_message(msg)
            return occ_message

    @log
    def sign_hash_with_planetmint(self, data_to_sign: str) -> str:
        with self._lock:
            """
            @brief: Signs the hash with the planetmint private key
            @param data_to_sign: hash to sign
            @return: signature
            """
            msg = OSCMessage(f"{PREFIX_IHW}/ecdsaSignPlmnt", ",s", [data_to_sign])
            occ_message = self.occ_message_sender.send_message(msg)
            signature = occ_message.data[1]
            return signature

    @log
    def sign_hash_with_rddl(self, data_to_sign: str) -> str:
        with self._lock:
            """
            @brief: Signs the hash with the planetmint private key
            @param data_to_sign: hash to sign
            @return: signature
            """
            msg = OSCMessage(f"{PREFIX_IHW}/ecdsaSignRddl", ",s", [data_to_sign])
            occ_message = self.occ_message_sender.send_message(msg)
            signature = occ_message.data[1]
            return signature

    @log
    def create_optega_keypair(self, ctx: int) -> str:
        with self._lock:
            """
            @brief: Signs the hash with the planetmint private key
            @param ctx: define one of 4 context of Optega x
            @return: public key
            """
            msg = OSCMessage(f"{PREFIX_IHW}/optigaTrustXCreateSecret", ",is", [ctx, ""])
            occ_message = self.occ_message_sender.send_message(msg)
            pubkey = occ_message.data[1]
            return pubkey

    @log
    def sign_with_optega(self, ctx: int, data_to_sign: str, pubkey: str) -> str:
        with self._lock:
            """
            @brief: Signs the hash with the planetmint private key
            @param ctx: define one of 4 context of Optega x
            @param data_to_sign: hash to sign
            @param pubkey: Optega X Security Chip Public Key
            @return: signature

            """
            msg = OSCMessage(f"{PREFIX_IHW}/optigaTrustXSignMessage", ",isss", [ctx, data_to_sign, pubkey, ""])
            occ_message = self.occ_message_sender.send_message(msg)
            signature = occ_message.data[1]
            return signature

    @log
    def unwrapPublicKey(self, public_key: str) -> tuple[bool, str]:
        if len(public_key) == 136:
            return True, public_key[-128:]
        if len(public_key) == 130:
            return True, public_key[-128:]
        elif len(public_key) == 128:
            return True, public_key
        else:
            return False, public_key

    @log
    def calculate_hash(self, data_to_sign: str) -> str:
        with self._lock:
            msg = OSCMessage(f"{PREFIX_IHW}/se050CalculateHash", ",s", [data_to_sign])
            occ_message = self.occ_message_sender.send_message(msg)
            return occ_message.data[1]

    @log
    def create_keypair_nist(self, ctx: int) -> str:
        with self._lock:
            """
            @brief: Signs the hash with the planetmint private key
            @param ctx: define one of 4 context of Optega x
            @return: public key
            """
            msg = OSCMessage(f"{PREFIX_IHW}/se050CreateKeyPair", ",ii", [ctx, 1])
            occ_message = self.occ_message_sender.send_message(msg)
            pubkey = occ_message.data[1]
            return pubkey

    @log
    def get_machine_id(self, ctx: int) -> str:
        with self._lock:
            """
            @brief: Get the public key from the slot
            @param ctx: define one of 4 context of Optega x
            @return: public key
            """
            msg = OSCMessage(f"{PREFIX_IHW}/se050GetPublicKey", ",i", [ctx])
            occ_message = self.occ_message_sender.send_message(msg)
            wrapped_pubkey = occ_message.data[1]
            (valid, pubKey) = self.unwrapPublicKey(wrapped_pubkey)
            if not valid:
                logger.error("Inject PlanetMintKey failed: No key found.")
            return pubKey

    @log
    def sign_with_nist(self, data_to_sign: str, ctx: int) -> str:
        with self._lock:
            """
            @brief: Signs the hash with the planetmint private key
            @param ctx: define one of 4 context of Optega x
            @param data_to_sign: hash to sign
            @param pubkey: Optega X Security Chip Public Key
            @return: signature

            """
            msg = OSCMessage(f"{PREFIX_IHW}/se050SignData", ",si", [data_to_sign, ctx])
            occ_message = self.occ_message_sender.send_message(msg)
            signature = occ_message.data[1]
            return signature

    @log
    def verify_nist_signature(self, data_to_sign: str, signature: str, ctx: int) -> bool:
        with self._lock:
            """
            @brief: Verifies the signature using the SE050 Security Chip
            @param data_to_sign: hash to verify
            @param signature: signature to verify
            @return: True if the signature is valid, False otherwise
            """
            msg = OSCMessage(f"{PREFIX_IHW}/se050VerifySignature", ",ssi", [data_to_sign, signature, ctx])
            occ_message = self.occ_message_sender.send_message(msg)
            return bool(occ_message.data[1])
