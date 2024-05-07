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
pubKey = trust_wallet.create_optega_keypair(slot)
print("Public key: " + pubKey)

hashBytes = getHash(pubKey.encode("utf-8"))
hashBytes.hex()

signature = trust_wallet.sign_with_optega(slot, hashBytes.hex(), pubKey)
print(signature[0])
