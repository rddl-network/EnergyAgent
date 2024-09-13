import ctypes
from ctypes import c_int, c_uint8, c_size_t, POINTER, byref, create_string_buffer
import sys

from app.RddlInteraction.TrustWallet.TrustWalletConnectorATECC608 import TrustWalletConnectorATECC608

trust_wallet = TrustWalletConnectorATECC608()


def print_hex_buffer(input):
    print(" ".join(f"{x:02X}" for x in input))


def write_atecc_config():
    status = trust_wallet.atecc608_lib.atecc_handler_init(0xC0, 1)
    if status:
        print(f"atecc_handler_init Fail! {status}")
        return

    ECCX08_DEFAULT_CONFIGURATION_VALS = (c_uint8 * 112)()  # Adjust the size accordingly
    status = trust_wallet.atecc608_lib.atecc_handler_write_configuration(ECCX08_DEFAULT_CONFIGURATION_VALS, 112)
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


def inject_priv_key():
    priv_key = (c_uint8 * 36)(
        0x00,
        0x00,
        0x00,
        0x00,
        0x39,
        0xAC,
        0x9B,
        0xF9,
        0x17,
        0x1D,
        0xE8,
        0x6F,
        0xFA,
        0x77,
        0xE0,
        0xB9,
        0x05,
        0x0B,
        0xF6,
        0xE0,
        0x6A,
        0x2C,
        0x1B,
        0xC1,
        0x76,
        0x79,
        0x36,
        0xE6,
        0xC7,
        0x45,
        0x79,
        0xE4,
        0x26,
        0xA4,
        0x47,
        0x5F,
    )

    slotID = 1
    pub_key = (c_uint8 * 64)()

    status = trust_wallet.atecc608_lib.atecc_handler_init(0xC0, 1)
    if status:
        print(f"atecc_handler_init Fail! {status}")
        return 0

    status = trust_wallet.atecc608_lib.atecc_handler_inject_priv_key(slotID, priv_key)
    if status:
        print(f"atecc_handler_inject_priv_key Fail! {status}")
        return 0

    status = trust_wallet.atecc608_lib.atecc_handler_get_public_key(slotID, pub_key)
    if status:
        print(f"atecc_handler_get_public_key Fail! {status}")
        return 0
    print("Pub key:")
    print_hex_buffer(pub_key)


if __name__ == "__main__":
    write_atecc_config()
    # provision_atecc()
    # inject_priv_key()
