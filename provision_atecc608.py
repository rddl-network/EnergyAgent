import ctypes
from ctypes import c_uint8, c_size_t, POINTER, byref, create_string_buffer
import binascii

from app.RddlInteraction.TrustWallet.TrustWalletConnectorATECC608 import TrustWalletConnectorATECC608

trust_wallet = TrustWalletConnectorATECC608()


def print_hex_buffer(input):
    print("".join([f"{x:02x}" for x in input]))


def write_atecc_config():
    status = trust_wallet.write_atecc_config()
    if status:
        print(f"atecc_handler_init Fail! {status}")
        return


def provision_atecc():
    slotID = 2
    pub_key = trust_wallet.create_keypair_nist(slotID)
    print("Pub key generated:")
    print(pub_key)

    pub_key_2 = trust_wallet.get_machine_id(slotID)
    print("Pub key:")
    print(pub_key_2)

    signature = trust_wallet.sign_with_nist(pub_key, slotID)
    print("Signature:")
    print(signature)

    valid = trust_wallet.verify_nist_signature(pub_key, signature, slotID)
    if not valid:
        print(f"atecc_handler_verify Fail!")
        return 0

    print("TEST ENDED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    # write_atecc_config()  # Uncomment this line to write the default configuration
    provision_atecc()
