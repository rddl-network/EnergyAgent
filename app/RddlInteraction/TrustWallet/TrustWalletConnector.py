import os
import sys
import platform
import threading
from osc4py3.oscbuildparse import OSCMessage

from app.RddlInteraction.TrustWallet.osc_message_sender import OSCMessageSender
from app.helpers.models import PlanetMintKeys
from app.helpers.logs import logger

PREFIX_IHW = "/IHW"


class TrustWalletConnector(object):
    _instance = None
    occ_message_sender = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        print("TrustWallet Demand")
        if not getattr(cls, "_instance", None):
            cls._instance = super().__new__(cls)
            cls._instance.__init__(*args, **kwargs)  # Call __init__ manually
        return cls._instance

    def __init__(self, port_name, timeout=100000):
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
            self.occ_message_sender = OSCMessageSender(lib_path, port_name, timeout=timeout)
        self.plmnt_keys = None

    def valise_get(self) -> str:
        with self._lock:
            """
            @brief: Gets the seed
            @return: return seed
            """
            msg = OSCMessage(f"{PREFIX_IHW}/getSeed", ",", [])
            occ_message = self.occ_message_sender.send_message(msg)
            return occ_message.data[1]

    # mnemonicToSeed

    def create_mnemonic(self):
        with self._lock:
            """
            @brief: Derives the private key from the mnemonic seed
            """
            self.plmnt_keys is None
            msg = OSCMessage(f"{PREFIX_IHW}/mnemonicToSeed", ",i", [1])
            occ_message = self.occ_message_sender.send_message(msg)
            print(occ_message)
            self.plmnt_keys = None
            return occ_message.data[1]

    def inject_planetmintkey_to_se050(self, slot: int):
        with self._lock:
            msg = OSCMessage(f"{PREFIX_IHW}/se050InjectSECPKeys", ",i", [slot])
            occ_message = self.occ_message_sender.send_message(msg)
            if occ_message.data[1] == "0":
                return True
            else:
                logger.error(f"Inject PlanetMintKey failed with errorcode {occ_message.data[1]}")
                return False

    def recover_from_mnemonic(self, mnemonic: str) -> str:
        with self._lock:
            """
            @brief: Derives the private key from the mnemonic seed
            """
            msg = OSCMessage(f"{PREFIX_IHW}/mnemonicToSeed", ",is", [1, mnemonic])
            occ_message = self.occ_message_sender.send_message(msg)
            self.plmnt_keys = None
            return occ_message.data[1]

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

    def get_seed_se050(self):
        with self._lock:
            msg = OSCMessage(f"{PREFIX_IHW}/se050GetSeed", ",", [])
            occ_message = self.occ_message_sender.send_message(msg)
            return occ_message

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

    def unwrapPublicKey(self, public_key: str) -> tuple[bool, str]:
        if len(public_key) == 136:
            return True, public_key[-128:]
        if len(public_key) == 130:
            return True, public_key[-128:]
        elif len(public_key) == 128:
            return True, public_key
        else:
            return False, public_key

    def calculate_hash(self, data_to_sign: str) -> str:
        with self._lock:
            msg = OSCMessage(f"{PREFIX_IHW}/se050CalculateHash", ",s", [data_to_sign])
            occ_message = self.occ_message_sender.send_message(msg)
            return occ_message.data[1]

    def create_se050_keypair_nist(self, ctx: int) -> str:
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

    def get_public_key_from_se050(self, ctx: int) -> str:
        with self._lock:
            """
            @brief: Get the public key from the slot
            @param ctx: define one of 4 context of Optega x
            @return: public key
            """
            msg = OSCMessage(f"{PREFIX_IHW}/se050GetPublicKey", ",i", [ctx])
            occ_message = self.occ_message_sender.send_message(msg)
            print(occ_message)
            wrapped_pubkey = occ_message.data[1]
            (valid, pubKey) = self.unwrapPublicKey(wrapped_pubkey)
            if not valid:
                logger.error("Inject PlanetMintKey failed: No key found.")
            return pubKey

    def sign_with_se050(self, data_to_sign: str, ctx: int) -> str:
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

    def verify_se050_signature(self, data_to_sign: str, signature: str, ctx: int) -> bool:
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
