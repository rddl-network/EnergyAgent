import platform
import sys
from fastapi import APIRouter

from app.RddlInteraction.TrustWallet.occ_messages import TrustWalletInteraction
from app.helpers.models import PlanetMintKeys

router = APIRouter(
    prefix="/twi",
    tags=["twi"],
    responses={404: {"detail": "Not found"}},
)

# system pick and optimistic architecture selection
if platform.system() == 'Linux':
    if platform.processor() == 'x86_64':
        trust_wallet = TrustWalletInteraction("lib/linux/x86_64/libocc.so", "/dev/ttyACM0")
    else:
        trust_wallet = TrustWalletInteraction("lib/linux/armv7/libocc.so", "/dev/ttyACM0")
elif platform.system() == 'Darwin':
    trust_wallet = TrustWalletInteraction("lib/macos/aarch/libpyocc.dylib", "/dev/ttyACM0")
else:
    sys.exit("unsupported OS, cannot load TA Wallet connector")
    
@router.get("/valise-get")
def valise_get():
    return trust_wallet.valise_get()


@router.get("/mnemonic")
def mnemonic_to_private_key():
    mnemonic = trust_wallet.create_mnemonic()
    return {"mnemonic": mnemonic}


@router.get("/recover-mnemonic/{mnemonic}")
def recover_mnemonic(mnemonic: str):
    mnemonic = trust_wallet.recover_from_mnemonic(mnemonic)
    return {"mnemonic": mnemonic}


@router.get("/get-planetmint-keys")
def get_planetmint_keys() -> PlanetMintKeys:
    planetmint_keys = trust_wallet.get_planetmint_keys()
    return planetmint_keys
