import hashlib
from app.RddlInteraction.TrustWallet.occ_messages import TrustWalletInteraction

trust_wallet = TrustWalletInteraction("/dev/ttyACM0")


def getHash(data: bytes) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(data)
    digest = hasher.digest()
    return digest


obj = trust_wallet.get_planetmint_keys()

data = b"\n\\\nZ\n#planetmintgo.asset.MsgNotarizeAsset\x123\n,plmnt19cl05ztgt8ey6v86hjjjn3thfmpu6q2xtveehc\x12\x03cid\x12^\nJ\nF\n\x1f/cosmos.crypto.secp256k1.PubKey\x12#\n!\x022\x8d\xe8x\x96\xb9\xcb\xb5\x10\x1c3_@\x02\x9eK\xe8\x98\x98\x8bG\n\xbb\xf6\x83\xf1\xa0\xb3\x18\xd74p\x18\x01\x12\x10\n\n\n\x05plmnt\x12\x012\x10\xc0\x9a\x0c\x1a\x0cplanetmintgo \x08"
hashedData = getHash(data)
signature = trust_wallet.sign_hash_with_planetmint(hashedData)
print("Signature: " + signature)
