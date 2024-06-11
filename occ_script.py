import time
import hashlib

import asn1

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


# trust_wallet.inject_planetmintkey_to_se050(2138)
# wrappedPubKey = trust_wallet.create_mnemonic()
# seed = trust_wallet.get_seed_SE050()
# pubkeys = trust_wallet.get_planetmint_keys()
# print(f"previouse seed: {seed}")
# print(f"previouse pubkeys: {pubkeys}")
# trust_wallet.recover_from_mnemonic('gown word egg athlete core marble laugh carpet border home adult giggle keep original decline fly hat ship obvious wrestle clip uncover grass cage')
# print(seed)
pubkeys_recovered = trust_wallet.get_planetmint_keys()
# seed_recovered = trust_wallet.get_seed_SE050()
# print(f"recovered seed: {seed_recovered}")
# print(f"recovered pubkeys: {pubkeys_recovered}")
# output = trust_wallet.inject_planetmintkey_to_se050(2138)
data_to_sign = "6bc7f47039987062ffbeb1accd12f723056fe92e37aa92cc433660d13f562d99"
# new_sign = trust_wallet.sign_with_se050(data_to_sign, 2138)
# # print(f'New sign: {new_sign}')
# # new_sign = '304402200e3e27df1c059da0314481c576a1c6528e6a163e45a1bfe1a9a59e9e14298d040220199fb176f0b271951e9c975f66c7aea6d74c5b9e2eb7da264c23c762e682cfe3'
# decoder = asn1.Decoder()
# new_sign_bytes = bytes.fromhex(new_sign)
# decoder.start(new_sign_bytes)
# tag, value = decoder.read()
# signature = binascii.hexlify(value).decode('utf-8')
# print(signature)
old_sign = trust_wallet.sign_hash_with_planetmint(data_to_sign=data_to_sign)
print(f"Old sign: {old_sign}")
# signature = "3044" + "0220" + old_sign[0][0:64] + "0220" + old_sign[0][64:]
# print(signature)
# valid = trust_wallet.verify_SE050_signature(data_to_sign, new_sign, 2138)
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
