from fastapi import APIRouter

from app.dependencies import trust_wallet
from app.helpers.models import PlanetMintKeys

router = APIRouter(
    prefix="/twi",
    tags=["twi"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/valise-get")
def valise_get():
    return trust_wallet.valise_get()


@router.get("/mnemonic")
def mnemonic_to_private_key():
    mnemonic = trust_wallet.create_mnemonic()
    return {"mnemonic": mnemonic}


@router.get("/recover-mnemonic/")
def recover_mnemonic(mnemonic: str):
    mnemonic = trust_wallet.recover_from_mnemonic(mnemonic)
    return {"mnemonic": mnemonic}


@router.get("/get-planetmint-keys")
def get_planetmint_keys() -> PlanetMintKeys:
    planetmint_keys = trust_wallet.get_planetmint_keys()
    return planetmint_keys
