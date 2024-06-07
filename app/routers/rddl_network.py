from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.RddlInteraction.cid_tool import store_cid
from app.dependencies import trust_wallet_instance, config
from app.RddlInteraction.TrustWallet.osc_message_sender import is_not_connected
from app.RddlInteraction.planetmint_interaction import (
    createAccountOnNetwork,
    getAccountInfo,
    attestMachine,
    notarizeAsset,
    computeMachineIDSignature,
    getMachineInfo,
    broadcastTX,
    getBalance,
)


router = APIRouter(
    prefix="/rddl",
    tags=["rddl"],
    responses={404: {"detail": "Not found"}},
)


@router.get("/createaccount")
async def createAccount():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        machine_id = config.machine_id
        address = trust_wallet_instance.get_planetmint_keys().planetmint_address
        signature = computeMachineIDSignature(machine_id)

        response = createAccountOnNetwork(config.ta_base_url, machine_id, address, signature)
        print(response)
        return {"status": "success", "message": str(response)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/account")
async def getAccount():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        print(keys.planetmint_address)
        accountID, sequence, status = getAccountInfo(config.planetmint_api, keys.planetmint_address)
        print(accountID)
        print(sequence)
        if status != "":
            return {"status": "error", "error": status, "message": status}
        else:
            return {"status": "success", "accountinfo": {"accountid": str(accountID), "sequence": str(sequence)}}
    except Exception as e:
        return {"status": "error", "error": str(e), "message": str(e)}


@router.get("/machine")
async def getMachineAttestation():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        machine_data, status = getMachineInfo(config.planetmint_api, keys.planetmint_address)
        if status != "":
            return {"status": "error", "error": status, "message": status}
        else:
            return {"status": "success", "machine": machine_data}
    except Exception as e:
        return {"status": "error", "error": str(e), "message": str(e)}


@router.get("/attestmachine")
async def getAttestMachine():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        accountID, sequence, status = getAccountInfo(config.planetmint_api, keys.planetmint_address)
        additionalCID = ""
        machineIDSig = computeMachineIDSignature(config.machine_id)
        print(machineIDSig)
        gps_data = '{"Latitude":"-48.876667","Longitude":"-123.393333"}'
        deviceDefinition = '{"Manufacturer": "RDDL","Serial":"AdnT2uyt"}'

        machine_attestation_tx = attestMachine(
            keys.planetmint_address,
            "EnergyAgent0",
            keys.extended_planetmint_pubkey,
            keys.extended_liquid_pubkey,
            gps_data,
            deviceDefinition,
            config.machine_id,
            machineIDSig,
            additionalCID,
            config.chain_id,
            accountID,
            sequence,
        )
        response = broadcastTX(machine_attestation_tx)

        if response.status_code != 200:
            return {"status": "error", "error": response.reason, "message": response.text}
        else:
            return {"status": "success", "message": response.text}
    except Exception as e:
        return {"status": "error", "error": str(e), "message": str(e)}


@router.get("/notarize")
async def notarize():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        payload = '{"Time": "' + str(datetime.now()) + '" }'
        cid = store_cid(payload)
        accountID, sequence, status = getAccountInfo(config.planetmint_api, keys.planetmint_address)
        notarize_tx = notarizeAsset(cid, config.chain_id, accountID, sequence)
        response = broadcastTX(notarize_tx)

        if response.status_code != 200:
            return {"status": "error", "error": response.reason, "message": response.text}
        else:
            return {"status": "success", "message": response.text}
    except Exception as e:
        return {"status": "error", "error": str(e), "message": str(e)}


@router.get("/balance/{address}")
async def get_balance(address: str):
    try:
        balance = getBalance(address)
        return {"status": "success", "balance": balance}
    except Exception as e:
        return {"status": "error", "message": str(e)}
