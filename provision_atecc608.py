import ctypes
from ctypes import c_int, c_uint8, c_size_t, POINTER, byref, create_string_buffer
import binascii

from app.RddlInteraction.TrustWallet.TrustWalletConnectorATECC608 import TrustWalletConnectorATECC608
from app.RddlInteraction.rddl.signing import getHash

trust_wallet = TrustWalletConnectorATECC608()


def print_hex_buffer(input):
    print(''.join([f"{x:02x}" for x in input]))


def write_atecc_config():
    status = trust_wallet.atecc608_lib.atecc_handler_init(0xC0, 1)
    if status:
        print(f"atecc_handler_init Fail! {status}")
        return

    status = trust_wallet.atecc608_lib.atecc_handler_write_default_configuration()
    if status:
        print(f"atecc_handler_write_configuration Fail! {status}")
        return

    # status = trust_wallet.atecc608_lib.atecc_handler_lock_zone(0)
    # if status:
    #     print(f"atecc_handler_lock_zone Fail! {status}")
    #     return


def provision_atecc():
    status = trust_wallet.atecc608_lib.atecc_handler_init(0xC0, 1)
    if status:
        print(f"atecc_handler_init Fail! {status}")
        return 0

    slotID = 1
    pub_key = (c_uint8 * 64)()
    status = trust_wallet.atecc608_lib.atecc_handler_genkey(slotID, pub_key)
    if status:
        print(f"atecc_handler_genkey Fail! {status}")
        return 0
    print("Pub key generated:")
    print_hex_buffer(pub_key)

    status = trust_wallet.atecc608_lib.atecc_handler_get_public_key(slotID, pub_key)
    if status:
        print(f"atecc_handler_get_public_key Fail! {status}")
        return 0
    print("Pub key:")
    print_hex_buffer(pub_key)

    signature = (c_uint8 * 64)()

    status = trust_wallet.atecc608_lib.atecc_handler_sign(slotID, pub_key, signature)
    if status:
        print(f"atecc_handler_sign Fail! {status}")
        return 0
    print("Signature:")
    print_hex_buffer(signature)

    status = trust_wallet.atecc608_lib.atecc_handler_verify(slotID, pub_key, signature, pub_key)
    if status:
        print(f"atecc_handler_verify Fail! {status}")
        return 0

    print("TEST ENDED SUCCESSFULLY!")
    return 0


if __name__ == "__main__":
    # write_atecc_config()  # Uncomment this line to write the default configuration
    provision_atecc()
