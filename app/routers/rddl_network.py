import subprocess
import re
from app.RddlInteraction.planetmint_interaction import createAccountOnNetwork, getAccountInfo, attestMachine, notarizeAsset, computeMachineIDSignature
from app.dependencies import trust_wallet_instance
from fastapi import APIRouter, Form

router = APIRouter(
    prefix="/rddl",
    tags=["rddl"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/createaccount")
async def createAccount():
    try:
        machine_id = "af837636231cf339f9e991ef37e12f56b04b824914acc2f04417e3894181c152ff2c2e9d785104301b2ee2a6d10578324de92cdf5f8d952f6fe1497d59c096e8"
        address = trust_wallet_instance.get_planetmint_keys().planetmint_address
        signature = computeMachineIDSignature( machine_id )

        response = createAccountOnNetwork("http://localhost:8080",machine_id, address, signature)
        return {"status": "success", "message": str(response)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/account")
async def getAccount():
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        print( keys.planetmint_address)
        accountID, sequence, status = getAccountInfo("http://localhost:1317", keys.planetmint_address)
        print( accountID)
        print( sequence)
        if status != "":
            return {"status": "error", "error": status, "message": status}
        else:
            return {"status": "success", "accountinfo": {"accountid": str(accountID), "sequence": str(sequence)} }
    except Exception as e:
        return {"status": "error", "error": str(e), "message": str(e)}