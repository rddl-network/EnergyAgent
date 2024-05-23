from osc4py3.oscbuildparse import OSCMessage

from app.RddlInteraction.TrustWallet.osc_message_sender import OSCMessageSender
from app.dependencies import config
from app.helpers.models import PlanetMintKeys
import platform
import sys

PREFIX_IHW = "/IHW"


class TrustWalletInteraction:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.__init__(*args, **kwargs)
        return cls._instance

    def __init__(self):
        if platform.system() == "Linux":
            if platform.processor() == "x86_64":
                lib_path = "app/lib/linux/x86_64/libocc.so"
            else:
                lib_path = "app/lib/linux/armv7/libocc.so"
        elif platform.system() == "Darwin":
            lib_path = "app/lib/macos/aarch/libpyocc.dylib"
        else:
            sys.exit("unsupported OS, cannot load TA Wallet connector")
        self.occ_message_sender = OSCMessageSender(lib_path, config.trust_wallet_port)

    def valise_get(self) -> str:
        """
        @brief: Gets the seed
        @return: return seed
        """
        msg = OSCMessage(f"{PREFIX_IHW}/getSeed", ",", [])
        occ_message = self.occ_message_sender.send_message(msg)
        return occ_message.data[1]

    # mnemonicToSeed

    def create_mnemonic(self):
        """
        @brief: Derives the private key from the mnemonic seed
        """
        msg = OSCMessage(f"{PREFIX_IHW}/mnemonicToSeed", ",i", [0])
        occ_message = self.occ_message_sender.send_message(msg)
        return occ_message.data[1]

    def recover_from_mnemonic(self, mnemonic: str) -> str:
        """
        @brief: Derives the private key from the mnemonic seed
        """
        msg = OSCMessage(f"{PREFIX_IHW}/mnemonicToSeed", ",is", [0, mnemonic])
        occ_message = self.occ_message_sender.send_message(msg)
        return occ_message.data[1]

    def get_planetmint_keys(self) -> PlanetMintKeys:
        """
        @brief: Gets the seed
        @return: return seed
        """
        msg = OSCMessage(f"{PREFIX_IHW}/getPlntmntKeys", ",", [])
        occ_message = self.occ_message_sender.send_message(msg)
        plmnt_keys = PlanetMintKeys()
        plmnt_keys.planetmint_address = occ_message.data[1]
        plmnt_keys.extended_planetmint_pubkey = occ_message.data[2]
        plmnt_keys.extended_liquid_pubkey = occ_message.data[3]
        return plmnt_keys

    def sign_hash_with_planetmint(self, data_to_sign: str) -> str:
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
        """
        @brief: Signs the hash with the planetmint private key
        @param ctx: define one of 4 context of Optega x
        @return: public key
        """
        msg = OSCMessage(f"{PREFIX_IHW}/optigaTrustXCreateSecret", ",i", [ctx])
        occ_message = self.occ_message_sender.send_message(msg)
        pubkey = occ_message.data[1]
        return pubkey

    def sign_with_optega(self, ctx: int, data_to_sign: str, pubkey: str) -> str:
        """
        @brief: Signs the hash with the planetmint private key
        @param ctx: define one of 4 context of Optega x
        @param data_to_sign: hash to sign
        @param pubkey: Optega X Security Chip Public Key
        @return: signature

        """
        msg = OSCMessage(f"{PREFIX_IHW}/optigaTrustXSignMessage", ",iss", [ctx, data_to_sign, pubkey])
        occ_message = self.occ_message_sender.send_message(msg)
        signature = occ_message.data[1]
        return signature
