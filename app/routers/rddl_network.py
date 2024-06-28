import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import conint

from app.RddlInteraction.utils import table_pagination
from app.db.tx_store import insert_tx
from app.db.activity_store import insert_tx_activity_by_response, get_all_activities
from app.RddlInteraction.cid_tool import store_cid
from app.dependencies import trust_wallet_instance, config
from app.RddlInteraction.TrustWallet.osc_message_sender import is_not_connected
from app.RddlInteraction.rddl_network_config import get_rddl_network_settings
from app.RddlInteraction.api_queries import (
    createAccountOnNetwork,
    getAccountInfo,
    getMachineInfo,
    getBalance,
)
from app.RddlInteraction.planetmint_interaction import (
    computeMachineIDSignature,
    getAttestMachineTx,
    getNotarizeAssetTx,
    getRedeemClaimsTx,
    broadcastTX,
    pre_attest_slot,
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
        machine_id = trust_wallet_instance.get_public_key_from_se050(pre_attest_slot)
        address = trust_wallet_instance.get_planetmint_keys().planetmint_address
        signature = computeMachineIDSignature(machine_id)

        response = createAccountOnNetwork(config.rddl.ta_base_url, machine_id, address, signature)
        print(response)
        if response.status_code == 200:
            return {"status": "success", "message": response.reason + " " + response.text}
        else:
            return {"status": "error", "message": response.reason + " " + response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/account")
async def getAccount():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        print(keys.planetmint_address)
        accountID, sequence, status = getAccountInfo(config.rddl.planetmint_api, keys.planetmint_address)
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
        machine_data, status = getMachineInfo(config.rddl.planetmint_api, keys.planetmint_address)
        if status != "":
            return {"status": "error", "error": status, "message": status}
        else:
            return {"status": "success", "machine": machine_data}
    except Exception as e:
        return {"status": "error", "error": str(e), "message": str(e)}


@router.get("/attestmachine")
async def getAttestMachine(name: str, additional_info: str):
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        machine_id = trust_wallet_instance.get_public_key_from_se050(pre_attest_slot)
        accountID, sequence, status = getAccountInfo(config.rddl.planetmint_api, keys.planetmint_address)
        additionalCID = ""
        machineIDSig = computeMachineIDSignature(machine_id)
        gps_data = fetch_gps_data()

        device_definition = json.dumps({"additional_information": additional_info})

        machine_attestation_tx = getAttestMachineTx(
            keys.planetmint_address,
            name,
            keys.extended_planetmint_pubkey,
            keys.extended_liquid_pubkey,
            gps_data,
            device_definition,
            machine_id,
            machineIDSig,
            additionalCID,
            config.rddl.chain_id,
            accountID,
            sequence,
        )
        response = broadcastTX(machine_attestation_tx, config.rddl.planetmint_api)
        insert_tx_activity_by_response(response, "Attest Machine")
        if response.status_code != 200:
            return {"status": "error", "error": response.reason, "message": response.text}
        return {"status": "success", "message": response.text}
    except Exception as e:
        return {"status": "error", "error": str(e), "message": str(e)}


def fetch_gps_data():
    url = "https://us-central1-rddl-io-8680.cloudfunctions.net/geolocation-888954d"
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes

        payload = response.json()  # Parse JSON response
        print(response.status_code)
        print(payload)

        if payload:
            return json.dumps(payload)
        else:
            print("Latitude or Longitude not found in the response.")
            return None
    except requests.RequestException as e:
        print(f"HTTP request failed: {e}")
        return None


@router.get("/notarize")
async def notarize():
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        payload = '{"Time": "' + str(datetime.now()) + '" }'
        cid = store_cid(payload)
        accountID, sequence, status = getAccountInfo(config.rddl.planetmint_api, keys.planetmint_address)
        notarize_tx = getNotarizeAssetTx(cid, config.rddl.chain_id, accountID, sequence)
        response = broadcastTX(notarize_tx, config.rddl.planetmint_api)
        tx_hash = json.loads(response.text)["tx_response"]["txhash"]
        insert_tx(tx_hash, cid)
        insert_tx_activity_by_response(response, "notarize CID")
        if response.status_code != 200:
            return {"status": "error", "error": response.reason, "message": response.text}
        return {"status": "success", "message": response.text}
    except Exception as e:
        return {"status": "error", "error": str(e), "message": str(e)}


@router.get("/redeemclaims/{beneficiary}")
async def redeemClaims(beneficiary: str):
    if is_not_connected(config.trust_wallet_port):
        raise HTTPException(status_code=400, detail="wallet not connected")
    try:
        keys = trust_wallet_instance.get_planetmint_keys()
        accountID, sequence, status = getAccountInfo(config.rddl.planetmint_api, keys.planetmint_address)
        redeem_claims_tx = getRedeemClaimsTx(beneficiary, config.rddl.chain_id, accountID, sequence)
        response = broadcastTX(redeem_claims_tx, config.rddl.planetmint_api)
        insert_tx_activity_by_response(response, "redeem claims")
        if response.status_code != 200:
            return {"status": "error", "error": response.reason, "message": response.text}
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


@router.get("/configuration")
async def get_configuration():
    return {"status": "success", "configuration": config.rddl}


@router.post("/configuration/{name}")
async def set_configuration(name: str):
    if name == "mainnet" or name == "testnet":
        config.rddl = get_rddl_network_settings(name)
        return {"status": "success", "configuration": config.rddl}
    return {"status": "error", "message": "configuration name is not supported - use 'mainnet' or 'testnet'."}


@router.get("/activities")
async def get_activities(
    page: Optional[conint(gt=0)] = None,  # page > 0
    page_size: Optional[conint(gt=0)] = None,  # page_size > 0
) -> List[Dict]:
    activities = get_all_activities()
    if not activities:
        return []

    activities_table = [
        {"type": a[0], "tx": a[1], "command": a[2], "result": a[3], "context": a[4], "timestamp": a[5]}
        for a in activities
    ]

    return table_pagination(page, page_size, activities_table)
