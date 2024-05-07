import time
import sys
import platform
import hashlib
from app.RddlInteraction.TrustWallet.occ_messages import TrustWalletInteraction

# system pick and optimistic architecture selection
if platform.system() == "Linux":
    if platform.processor() == "x86_64":
        trust_wallet = TrustWalletInteraction("lib/linux/x86_64/libocc.so", "/dev/ttyACM0")
    else:
        trust_wallet = TrustWalletInteraction("lib/linux/armv7/libocc.so", "/dev/ttyACM0")
elif platform.system() == "Darwin":
    trust_wallet = TrustWalletInteraction("lib/macos/aarch/libpyocc.dylib", "/dev/ttyACM0")
else:
    sys.exit("unsupported OS, cannot load TA Wallet connector")


def getHash(data: bytes) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(data)
    digest = hasher.digest()
    return digest


slot = 2
wrappedPubKey = trust_wallet.create_optega_keypair(slot)
(valid, pubKey) = trust_wallet.unwrappPublicKey( wrappedPubKey )
if valid == False:
    exit(-1)
    
print("Public key: " + pubKey)
print("Public key(len): " + str(len(pubKey)))
time.sleep(2)

hashBytes = getHash(pubKey.encode("utf-8"))
hashBytes.hex()

signature = trust_wallet.sign_with_optega(slot, hashBytes.hex(), pubKey)
print(signature[0])
