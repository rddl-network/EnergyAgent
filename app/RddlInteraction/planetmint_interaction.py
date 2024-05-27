import requests
import json
import base64
import hashlib
from typing import Tuple

from app.proto.planetmintgo.machine import tx_pb2 as MachineTx
from app.RddlInteraction.rddl import planetmint
from app.RddlInteraction.rddl import signing
from app.dependencies import trust_wallet_instance, config
import binascii


def getHash(data: bytes) -> bytes:
    hasher = hashlib.sha256()
    hasher.update(data)
    digest = hasher.digest()
    return digest


def create_tx_notarize_data(cid: str) -> str:
    keys = trust_wallet_instance.get_planetmint_keys()
    account_id, sequence, status = getAccountInfo(config.planetmint_api, keys.planetmint_address)
    notarize_tx = notarizeAsset(cid, config.chain_id, account_id, sequence)
    response = broadcastTX(notarize_tx)
    return f"notarize data {cid} to {keys.planetmint_address} with response {response.text}"


def computeMachineIDSignature(publicKey: str) -> str:
    hashBytes = getHash(binascii.unhexlify(publicKey))
    signature = trust_wallet_instance.sign_with_optega(2, hashBytes.hex(), publicKey)
    signature = "30" + hex(int(len(signature) / 2))[2:] + signature
    return signature


def createAccountOnNetwork(
    ta_service_base_url: str, machineId: str, plmnt_address: str, signature: str
) -> requests.Response:
    # Define the URL and data
    url = ta_service_base_url + "/create-account"
    data = {"machine-id": machineId, "plmnt-address": plmnt_address, "signature": signature}

    # Set headers
    headers = {"Content-Type": "application/json"}

    # Send POST request with JSON data and headers
    response = requests.post(url, json=data, headers=headers)
    return response


def getAccountInfo(apiURL: str, address: str) -> Tuple[int, int, str]:
    queryURL = apiURL + "/cosmos/auth/v1beta1/account_info/" + address
    headers = {"Content-Type": "application/json"}

    # Send POST request with JSON data and headers
    response = requests.get(queryURL, headers=headers)

    accountID = 0
    sequence = 0
    statusMsg = ""
    if response.status_code != 200:
        statusMsg = response.text
    else:
        data = json.loads(response.text)
        accountID = int(data["info"]["account_number"])
        sequence = int(data["info"]["sequence"])
        statusMsg = ""

    return (accountID, sequence, statusMsg)


def getMachineInfo(apiURL: str, address: str) -> Tuple[str, str]:
    queryURL = apiURL + "/planetmint/machine/address/" + address
    headers = {"Content-Type": "application/json"}

    # Send POST request with JSON data and headers
    response = requests.get(queryURL, headers=headers)

    machinedata = ""
    statusMsg = ""
    if response.status_code != 200:
        statusMsg = response.text
    else:
        machinedata = json.loads(response.text)
        statusMsg = ""

    return (machinedata, statusMsg)


def attestMachine(
    plmnt_address: str,
    name: str,
    issuerPlanetmint: str,
    issuerLiquid: str,
    gps: str,
    deviceDefinition: str,
    machineID: str,
    signature: str,
    additionalCID: str,
    chainID: str,
    accountID: int,
    sequence: int,
) -> str:
    attestMachine = MachineTx.MsgAttestMachine()
    attestMachine.creator = plmnt_address
    attestMachine.machine.name = name
    attestMachine.machine.ticker = ""
    attestMachine.machine.domain = ""
    attestMachine.machine.reissue = False
    attestMachine.machine.amount = 0
    attestMachine.machine.precision = 0
    attestMachine.machine.issuerPlanetmint = issuerPlanetmint
    attestMachine.machine.issuerLiquid = issuerLiquid
    attestMachine.machine.machineId = machineID
    attestMachine.machine.metadata.additionalDataCID = additionalCID
    attestMachine.machine.metadata.gps = gps
    attestMachine.machine.metadata.assetDefinition = '{"Version": "0.1"}'
    attestMachine.machine.metadata.device = deviceDefinition
    attestMachine.machine.type = 1  # RDDL_MACHINE_POWER_SWITCH
    attestMachine.machine.address = plmnt_address
    attestMachine.machine.machineIdSignature = signature

    anyMsg = planetmint.getAnyMachineAttestation(attestMachine)
    mycoin4Fee = planetmint.getCoin("plmnt", "0")

    txString = createAndSignEnvelopeMessage(anyMsg, mycoin4Fee, chainID, accountID, sequence)
    return txString


def createAndSignEnvelopeMessage(anyMsg: any, coin: any, chainID: str, accountID: int, sequence: int) -> str:
    PlanetmintKeys = trust_wallet_instance.get_planetmint_keys()

    pubKeyBytes = binascii.unhexlify(PlanetmintKeys.raw_planetmint_pubkey)
    rawTx = planetmint.getRawTx(anyMsg, coin, pubKeyBytes, sequence)
    signDoc = planetmint.getSignDoc(rawTx, chainID, accountID)
    signDocBytes = signDoc.SerializeToString()

    hash = signing.getHash(signDocBytes)
    hash_string = binascii.hexlify(hash).decode("utf-8")
    signature_hexed_string = trust_wallet_instance.sign_hash_with_planetmint(hash_string)
    sig_bytes = binascii.unhexlify(signature_hexed_string.encode("utf-8"))
    rawTx.signatures.append(sig_bytes)
    rawTxBytes = rawTx.SerializeToString()

    encoded_string = base64.b64encode(rawTxBytes)
    finalString = encoded_string.decode("utf-8")

    return finalString


def notarizeAsset(cid: str, chainID: str, accountID: int, sequence: int) -> str:
    PlanetmintKeys = trust_wallet_instance.get_planetmint_keys()

    coin4Fee = planetmint.getCoin("plmnt", "1")
    anyMsg = planetmint.getAnyAsset(PlanetmintKeys.planetmint_address, cid)

    txString = createAndSignEnvelopeMessage(anyMsg, coin4Fee, chainID, accountID, sequence)
    return txString


def broadcastTX(tx_bytes: str) -> requests.Response:
    url = config.planetmint_api + "/cosmos/tx/v1beta1/txs"

    data = {"tx_bytes": tx_bytes, "mode": "BROADCAST_MODE_SYNC"}

    # Set headers
    headers = {"Content-Type": "application/json"}

    # Send POST request with JSON data and headers
    response = requests.post(url, json=data, headers=headers)
    print(response.status_code)
    print(response.text)
    return response


def getBalance(address: str) -> dict:
    url = f"{config.planetmint_api}/cosmos/bank/v1beta1/balances/{address}"
    headers = {"Content-Type": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to get balance: {response.text}")

    data = json.loads(response.text)
    balance = data["balances"]
    return balance
