from fastapi import APIRouter, HTTPException

from app.RddlInteraction.TrustWallet.osc_message_sender import is_not_connected
from app.RddlInteraction.planetmint_interaction import pre_attest_slot
from app.dependencies import trust_wallet_instance, config
from app.helpers.models import PlanetMintKeys

router = APIRouter(
    prefix="/twi",
    tags=["twi"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/valise-get")
def valise_get():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    return trust_wallet_instance.valise_get()


@router.get("/mnemonic")
def mnemonic_to_private_key():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    mnemonic = trust_wallet_instance.create_mnemonic()
    return {"mnemonic": mnemonic}


@router.get("/recover-mnemonic/")
def recover_mnemonic(mnemonic: str):
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    mnemonic = trust_wallet_instance.recover_from_mnemonic(mnemonic)
    return {"mnemonic": mnemonic}


@router.get("/get-planetmint-keys")
def get_planetmint_keys() -> PlanetMintKeys:
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    planetmint_keys = trust_wallet_instance.get_planetmint_keys()
    return planetmint_keys


@router.get("/get-machine-id")
def get_machine_id() -> str:
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    machine_id = trust_wallet_instance.get_public_key_from_se050(pre_attest_slot)
    return machine_id
