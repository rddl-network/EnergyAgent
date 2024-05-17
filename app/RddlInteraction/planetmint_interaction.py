import requests
import json
import base64
from typing import Tuple

from planetmintgo.machine import tx_pb2 as MachineTx
from app.RddlInteraction.rddl import planetmint
from app.RddlInteraction.rddl import signing
from app.RddlInteraction.TrustWallet.occ_messages import TrustWalletInteraction
import binascii


def create_tx_notarize_data(cid: str, address: str) -> str:
    # TODO: implement this function
    return f"notarize data {cid} to {address}"


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

    trust_wallet = TrustWalletInteraction("/dev/ttyACM0")
    PlanetmintKeys = trust_wallet.get_planetmint_keys()

    attestMachine = MachineTx.MsgAttestMachine()
    attestMachine.creator = PlanetmintKeys.planetmint_address
    attestMachine.machine.name = name
    attestMachine.machine.issuerPlanetmint = (
        PlanetmintKeys.extended_planetmint_pubkey
    )  # "02328de87896b9cbb5101c335f40029e4be898988b470abbf683f1a0b318d73470"
    attestMachine.machine.issuerLiquid = (
        PlanetmintKeys.extended_liquid_pubkey
    )  # "xpub661MyMwAqRbcEigRSGNjzqsUbkoxRHTDYXDQ6o5kq6EQTSYuXxwD5zNbEXFjCG3hDmYZqCE4HFtcPAi3V3MW9tTYwqzLDUt9BmHv7fPcWaB"
    attestMachine.machine.machineId = machineID  # "02328de87896b9cbb5101c335f40029e4be898988b470abbf683f1a0b318d73470"
    attestMachine.machine.metadata.additionalDataCID = additionalCID
    attestMachine.machine.metadata.gps = gps  # "{\"Latitude\":\"-48.876667\",\"Longitude\":\"-123.393333\"}"
    attestMachine.machine.metadata.assetDefinition = '{"Version": "0.1"}'
    attestMachine.machine.metadata.device = deviceDefinition  # "{\"Manufacturer\": \"RDDL\",\"Serial\":\"AdnT2uyt\"}"
    attestMachine.machine.type = 1  # RDDL_MACHINE_POWER_SWITCH
    attestMachine.machine.machineIdSignature = signature
    attestMachine.machine.address = PlanetmintKeys.planetmint_address

    anyMsg = planetmint.getAnyMachineAttestation(attestMachine)
    coin4Fee = planetmint.getCoin("plmnt", "0")

    pubKeyBytes = binascii.unhexlify(PlanetmintKeys.raw_planetmint_pubkey)
    rawTx = planetmint.getRawTx(anyMsg, coin4Fee, pubKeyBytes, sequence)
    signDoc = planetmint.getSignDoc(rawTx, chainID, accountID)
    signDocBytes = signDoc.SerializeToString()

    hash = signing.getHash(signDocBytes)
    hash_string = binascii.hexlify(hash).decode("utf-8")
    signature_hexed_string = trust_wallet.sign_hash_with_planetmint(hash_string)
    # keybytes = bytes(reference_private_key[-32:])
    # signature_bytes = signing.signBytesWithKey( signDocBytes, keybytes )
    sig_bytes = binascii.unhexlify(signature_hexed_string.encode("utf-8"))
    rawTx.signatures.append(sig_bytes)
    rawTxBytes = rawTx.SerializeToString()
    encoded_string = base64.b64encode(rawTxBytes)
    finalString = encoded_string.decode("utf-8")
    return finalString
