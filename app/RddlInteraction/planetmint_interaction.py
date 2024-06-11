import requests
import json
import base64
import binascii


from app.dependencies import trust_wallet_instance
from app.proto.planetmintgo.dao import tx_pb2 as DaoTx
from app.proto.planetmintgo.machine import tx_pb2 as MachineTx
from app.RddlInteraction.rddl import planetmint, signing
from app.RddlInteraction.api_queries import getAccountInfo

planetmint_slot = 2138


def create_tx_notarize_data(cid: str, planetmint_api: str, chain_id: str) -> str:
    keys = trust_wallet_instance.get_planetmint_keys()
    account_id, sequence, status = getAccountInfo(planetmint_api, keys.planetmint_address)
    notarize_tx = getNotarizeAssetTx(cid, chain_id, account_id, sequence)
    response = broadcastTX(notarize_tx, planetmint_api)
    tx_hash = json.loads(response.text)["tx_response"]["txhash"]
    return tx_hash


def computeMachineIDSignature(publicKey: str) -> str:
    pre_attest_slot = 2
    hashBytes = signing.getHash(binascii.unhexlify(publicKey))
    signature = trust_wallet_instance.sign_with_se050(hashBytes.hex(), pre_attest_slot)
    return signature


def getAttestMachineTx(
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
    theFee = planetmint.getCoin("plmnt", "0")

    txString = createAndSignEnvelopeMessage(anyMsg, theFee, chainID, accountID, sequence)
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


def getNotarizeAssetTx(cid: str, chainID: str, accountID: int, sequence: int) -> str:
    PlanetmintKeys = trust_wallet_instance.get_planetmint_keys()

    theFee = planetmint.getCoin("plmnt", "1")
    anyMsg = planetmint.getAnyAsset(PlanetmintKeys.planetmint_address, cid)

    txString = createAndSignEnvelopeMessage(anyMsg, theFee, chainID, accountID, sequence)
    return txString


def broadcastTX(tx_bytes: str, planetmint_api: str) -> requests.Response:
    url = planetmint_api + "/cosmos/tx/v1beta1/txs"

    data = {"tx_bytes": tx_bytes, "mode": "BROADCAST_MODE_SYNC"}

    # Set headers
    headers = {"Content-Type": "application/json"}

    # Send POST request with JSON data and headers
    response = requests.post(url, json=data, headers=headers)
    print(response.status_code)
    print(response.text)
    return response


def getPoPResultTx(
    challengee: str, initiator: str, height: int, success: bool, chainID: str, accountID: int, sequence: int
) -> str:
    keys = trust_wallet_instance.get_planetmint_keys()

    pop_result = DaoTx.MsgReportPopResult()
    pop_result.creator = keys.planetmint_address
    pop_result.challenge.initiator = initiator
    pop_result.challenge.challenger = keys.planetmint_address
    pop_result.challenge.challengee = challengee
    pop_result.challenge.height = height
    pop_result.challenge.success = success
    pop_result.challenge.finished = False

    anyMsg = planetmint.getAnyPopResult(pop_result)
    theFee = planetmint.getCoin("plmnt", "1")
    txString = createAndSignEnvelopeMessage(anyMsg, theFee, chainID, accountID, sequence)
    return txString


def getRedeemClaimsTx(beneficiary: str, chainID: str, accountID: int, sequence: int) -> str:
    PlanetmintKeys = trust_wallet_instance.get_planetmint_keys()

    theFee = planetmint.getCoin("plmnt", "1")
    anyMsg = planetmint.getAnyRedeemClaimMsg(PlanetmintKeys.planetmint_address, beneficiary)

    txString = createAndSignEnvelopeMessage(anyMsg, theFee, chainID, accountID, sequence)
    return txString
