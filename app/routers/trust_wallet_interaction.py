from fastapi import APIRouter
from app.helpers.models import PlanetMintKeys
from app.dependencies import trust_wallet_instance

router = APIRouter(
    prefix="/twi",
    tags=["twi"],
    responses={404: {"detail": "Not found"}},
)



@router.get("/valise-get")
def valise_get():
    return trust_wallet_instance.valise_get()


@router.get("/mnemonic")
def mnemonic_to_private_key():
    mnemonic = trust_wallet_instance.create_mnemonic()
    return {"mnemonic": mnemonic}


@router.get("/recover-mnemonic/")
def recover_mnemonic(mnemonic: str):
    mnemonic = trust_wallet_instance.recover_from_mnemonic(mnemonic)
    return {"mnemonic": mnemonic}


@router.get("/get-planetmint-keys")
def get_planetmint_keys() -> PlanetMintKeys:
    planetmint_keys = trust_wallet_instance.get_planetmint_keys()
    return planetmint_keys
