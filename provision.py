import time
import hashlib
from app.RddlInteraction.rddl.signing import getHash
from app.RddlInteraction.TrustWallet.TrustWalletConnector import TrustWalletConnector
import binascii


trust_wallet = TrustWalletConnector("/dev/ttyACM0")


slot = 2
wrappedPubKey = trust_wallet.create_optega_keypair(slot)
(valid, pubKey) = trust_wallet.unwrapPublicKey(wrappedPubKey)
if valid == False:
    exit(-1)

print("Public key: " + pubKey)
print("Public key(len): " + str(len(pubKey)))
time.sleep(0.2)

hashBytes = getHash(binascii.unhexlify(pubKey))
print(hashBytes)
print(hashBytes.hex())
print(binascii.hexlify(hashBytes))
signature = trust_wallet.sign_with_optega(slot, hashBytes.hex(), pubKey)
print(signature)
