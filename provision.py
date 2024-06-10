import time
import hashlib
from app.RddlInteraction.rddl.signing import getHash
from app.RddlInteraction.TrustWallet.TrustWalletConnector import TrustWalletConnector
import binascii


trust_wallet = TrustWalletConnector("/dev/tty.usbmodem1101")


slot = 2
# wrappedPubKey = trust_wallet.create_SE050_keypair_secp256k1(slot)

wrappedPubKey = trust_wallet.create_SE050_keypair_nist(slot)
(valid, pubKey) = trust_wallet.unwrapPublicKey(wrappedPubKey)
if valid == False:
    exit(-1)

print("Wrapped Pubkey: " + wrappedPubKey)
print("Public key: " + pubKey)
print("Public key(len): " + str(len(pubKey)))
time.sleep(0.2)

hashBytes = getHash(binascii.unhexlify(pubKey))
print(hashBytes)
print(hashBytes.hex())
print(binascii.hexlify(hashBytes))
# data_hash = trust_wallet.calculate_hash(pubKey)
# print("Data Hash: " + data_hash)
signature = trust_wallet.sign_with_se050(hashBytes.hex(), slot)
print(signature)
