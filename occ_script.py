import time
import hashlib
from app.RddlInteraction.TrustWallet.TrustWalletConnector import TrustWalletConnector
import binascii


trust_wallet = TrustWalletConnector("/dev/tty.usbmodem1101")


def getHash(data: bytes) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(data)
    digest = hasher.digest()
    return digest


slot = 2
# wrappedPubKey = trust_wallet.create_SE050_keypair_secp256k1(slot)
# command='/se050GetSeed' data=[',s', 'b23fb35cd1cc9db6071278c40b82ee1375412fab12c9c51b1ef74888e5b239654d7f0d4c5a83108dc92aec4bbb0c136d9f87296dd04716a24bb29eb4d1b88bf7']
# command='/se050GetSeed' data=[',s', 'd379181d398ff9261154ab17563e300d7e3e4e2b487f2c78b3f4ec0d170ec6359b227f40cbcd14d3549b4060d7087c6dfeb915e6bdb65902dc8e42c815682f6c']


trust_wallet.inject_planetmintkey_to_se050(2138)
# wrappedPubKey = trust_wallet.create_mnemonic()
# seed = trust_wallet.get_seed_SE050()
pubkeys = trust_wallet.get_planetmint_keys()
# output = trust_wallet.inject_planetmintkey_to_se050(2138)
# valid = trust_wallet.verify_SE050_signature(hashBytes.hex(), signature, slot)
# print(valid)
# (valid, pubKey) = trust_wallet.unwrapPublicKey(wrappedPubKey)
# if valid == False:
#     exit(-1)
#
# print("Wrapped Pubkey: " + wrappedPubKey)
# print("Public key: " + pubKey)
# print("Public key(len): " + str(len(pubKey)))
# time.sleep(0.2)
#
# hashBytes = getHash(binascii.unhexlify(pubKey))
# print(hashBytes)
# print(hashBytes.hex())
# print(binascii.hexlify(hashBytes))
# signature = trust_wallet.sign_with_SE050(hashBytes.hex(), slot)
# print(signature)
# valid = trust_wallet.verify_SE050_signature(hashBytes.hex(), signature, slot)
# print(valid)
