from fastapi import APIRouter

from app.RddlInteraction.TrustWallet.occ_messages import TrustWalletInteraction
from app.helpers.models import PlanetMintKeys

router = APIRouter(
    prefix="/twi",
    tags=["twi"],
    responses={404: {"detail": "Not found"}},
)

trust_wallet = TrustWalletInteraction("libpyocc.dylib", "/dev/tty.usbmodem1101")


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


@router.get("/sign-hash-with-planetmint/{data_to_sign}")
def sign_hash_with_planetmint(data_to_sign: str):
    return trust_wallet.sign_hash_with_planetmint(data_to_sign)


@router.get("/sign_hash_with_rddl/{data_to_sign}")
def sign_hash_with_rddl(data_to_sign: str):
    return trust_wallet.sign_hash_with_rddl(data_to_sign)


@router.get("/create_optega_keypair/{ctx}")
def create_optega_keypair(ctx: int):
    return trust_wallet.create_optega_keypair(ctx)


@router.get("/sign_with_optega/{ctx}/{data_to_sign}/{pubkey}")
def sign_with_optega(ctx: int, data_to_sign: str, pubkey: str):
    return trust_wallet.sign_with_optega(ctx, data_to_sign, pubkey)
