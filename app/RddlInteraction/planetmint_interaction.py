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
    attestMachine.machine.metadata.assetDefinition = "{\"Version\": \"0.1\"}"
    attestMachine.machine.metadata.device = deviceDefinition  
    attestMachine.machine.type = 1  # RDDL_MACHINE_POWER_SWITCH
    attestMachine.machine.address = plmnt_address
    attestMachine.machine.machineIdSignature = signature
    

    anyMsg = planetmint.getAnyMachineAttestation(attestMachine)
    mycoin4Fee = planetmint.getCoin("plmnt", "1")

    txString = createAndSignEnvelopeMessage(anyMsg, mycoin4Fee, chainID, accountID, sequence)
    return txString


def createAndSignEnvelopeMessage(anyMsg: any, coin: any, chainID: str, accountID: int, sequence: int) -> str:
    trust_wallet = TrustWalletInteraction("/dev/ttyACM0")
    PlanetmintKeys = trust_wallet.get_planetmint_keys()

    pubKeyBytes = binascii.unhexlify(PlanetmintKeys.raw_planetmint_pubkey)
    rawTx = planetmint.getRawTx(anyMsg, coin, pubKeyBytes, sequence)
    signDoc = planetmint.getSignDoc(rawTx, chainID, accountID)
    signDocBytes = signDoc.SerializeToString()

    hash = signing.getHash(signDocBytes)
    hash_string = binascii.hexlify(hash).decode("utf-8")
    signature_hexed_string = trust_wallet.sign_hash_with_planetmint(hash_string)
    sig_bytes = binascii.unhexlify(signature_hexed_string.encode("utf-8"))
    rawTx.signatures.append(sig_bytes)
    rawTxBytes = rawTx.SerializeToString()
    encoded_string = base64.b64encode(rawTxBytes)
    finalString = encoded_string.decode("utf-8")
    return finalString
    

def notarizeAsset( cid: str, chainID: str, accountID: int, sequence: int ) -> str:
    trust_wallet = TrustWalletInteraction("/dev/ttyACM0")
    PlanetmintKeys = trust_wallet.get_planetmint_keys()
    
    coin4Fee = planetmint.getCoin("plmnt", "1")
    anyMsg = planetmint.getAnyAsset( PlanetmintKeys.planetmint_address, cid)
    
    txString = createAndSignEnvelopeMessage(anyMsg, coin4Fee, chainID, accountID, sequence)
    return txString