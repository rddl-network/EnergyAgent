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
    slotID = 1
    pub_key = trust_wallet.create_keypair_nist(slotID)
    print("Pub key generated:")
    print_hex_buffer(pub_key)

    status = trust_wallet.get_machine_id(slotID)
    if status:
        print(f"atecc_handler_get_public_key Fail! {status}")
        return 0
    print("Pub key:")
    print_hex_buffer(pub_key)

    signature = trust_wallet.sign_with_nist(pub_key, slotID)
    print("Signature:")
    print_hex_buffer(signature)

    status = trust_wallet.verify_nist_signature(pub_key, signature, slotID)
    if status:
        print(f"atecc_handler_verify Fail! {status}")
        return 0

    print("TEST ENDED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    # write_atecc_config()  # Uncomment this line to write the default configuration
    provision_atecc()
