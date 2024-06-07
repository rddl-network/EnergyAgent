import binascii
from app.RddlInteraction.api_queries import createAccountOnNetwork, getAccountInfo
from app.RddlInteraction.planetmint_interaction import attestMachine, notarizeAsset
from app.RddlInteraction.TrustWallet.TrustWalletConnector import TrustWalletConnector


def test_createMnemonic():
    trust_wallet = TrustWalletConnector("/dev/ttyACM0")
    mnemonic = trust_wallet.create_mnemonic()
    print(mnemonic)


def test_recoverMnemonic():
    trust_wallet = TrustWalletConnector("/dev/ttyACM0")
    recoverPhrase = "penalty police pool orphan snack faith educate syrup skill picnic prepare mystery dune control near nation report evolve ethics genius elite tool rigid crane"
    result = trust_wallet.recover_from_mnemonic(recoverPhrase)
    assert recoverPhrase == result


def test_createAccountOnNetwork():
    ta_base_url = "http://localhost:8080"

    # unprocessed TA input, not plmnt compatible
    machine_id = "6003d0ab9af4ec112629195a7266a244aecf1ac7691da0084be3e7ceea2ee71571b0963fffd9c80a640317509a681ac66c2ed70ecc9f317a0d2b1a9bff94ff74"
    address = "plmnt196ucf7y7t6x7kuvzlx5rpju5822efjelmn7xz0"
    signature = "022100e51cf02a0b900a36f78e8c1ff0562879469094e42ab44db137297c686a1d928e022100b84583ceda145d10d019b31b84a4f4d0e62700ae094204c9dabee17244b62926"

    # process TA input to be plmnt compatible
    signature = "30" + hex(int(len(signature) / 2))[2:] + signature

    response = createAccountOnNetwork(ta_base_url, machine_id, address, signature)
    print(response.status_code)
    print(response.text)


def test_getAccountInfo_Valid():
    accountID, sequence, statusText = getAccountInfo(
        "http://localhost:1317", "plmnt196ucf7y7t6x7kuvzlx5rpju5822efjelmn7xz0"
    )
    assert 10 == accountID
    assert 0 == sequence
    assert "" == statusText


def test_getAccountInfo_Invalid():
    accountID, sequence, statusText = getAccountInfo(
        "http://localhost:1317", "plmnt196ucf707t6x7kuvzlx5rpju5822efjelmn7xz0"
    )
    assert 0 == accountID
    assert 0 == sequence
    assert (
        '{"code":2,"message":"decoding bech32 failed: invalid checksum (expected xwetnc got mn7xz0)","details":[]}'
        == statusText
    )


reference_pub_key = bytearray(
    [
        0x02,
        0xEB,
        0x93,
        0xC1,
        0xE9,
        0x64,
        0xDD,
        0x58,
        0xD8,
        0x61,
        0x19,
        0x3B,
        0xF0,
        0x15,
        0xB0,
        0x74,
        0x38,
        0x1D,
        0x44,
        0x32,
        0x28,
        0x21,
        0xA7,
        0x9C,
        0x54,
        0xA2,
        0x0B,
        0x45,
        0x5B,
        0x4C,
        0x57,
        0xC1,
        0xC6,
    ]
)


def test_attestMachine_valid():

    trust_wallet = TrustWalletConnector("/dev/ttyACM0")
    recoverPhrase = "penalty police pool orphan snack faith educate syrup skill picnic prepare mystery dune control near nation report evolve ethics genius elite tool rigid crane"
    result = trust_wallet.recover_from_mnemonic(recoverPhrase)
    assert recoverPhrase == result

    expected_result = "CowGCokGCiYvcGxhbmV0bWludGdvLm1hY2hpbmUuTXNnQXR0ZXN0TWFjaGluZRLeBQoscGxtbnQxOTl6ZjB2a21laGhyMmhoZHQzZTQyNXI1ZHg0NzQ5ZG1lbm0zNXcSrQUKCk15TWFjaGluZTA6b3hwdWI2R2hKdG1zWjVUNnpGUEI5NjFZVlNwTUVrb0dRMk1jWUU1M0hRRGlxWXg1Yll3aUNtZ0FoZXdWSlNDVmtoMzhvVmVIdGFBVjlRSkoxYVNFSlpzemoxNGU4RzgzWkwzQ1ZTNWJkRHF1M25XbkJvcG1wYjd2VVRlQkdDRDVKdHo5enJyY3FXb01CWGRRVkVyMXFlYkpzWWdFVFhOZWJ1S21uek1pNFMyYk1xcEVzd0xVbUVhMnM2SGVYejhjZ1ZyZHNZVG5RVnRjeGJkNVZyN1pacHFtTUdYNlpUOHRRSoABNjAwM2QwYWI5YWY0ZWMxMTI2MjkxOTVhNzI2NmEyNDRhZWNmMWFjNzY5MWRhMDA4NGJlM2U3Y2VlYTJlZTcxNTcxYjA5NjNmZmZkOWM4MGE2NDAzMTc1MDlhNjgxYWM2NmMyZWQ3MGVjYzlmMzE3YTBkMmIxYTliZmY5NGZmNzRSdwozeyJMYXRpdHVkZSI6Ii00OC44NzY2NjciLCJMb25naXR1ZGUiOiItMTIzLjM5MzMzMyJ9Eix7Ik1hbnVmYWN0dXJlciI6ICJSRERMIiwiU2VyaWFsIjoiQWRuVDJ1eXQifRoSeyJWZXJzaW9uIjogIjAuMSJ9WAFikAEzMDQ2MDIyMTAwZTUxY2YwMmEwYjkwMGEzNmY3OGU4YzFmZjA1NjI4Nzk0NjkwOTRlNDJhYjQ0ZGIxMzcyOTdjNjg2YTFkOTI4ZTAyMjEwMGI4NDU4M2NlZGExNDVkMTBkMDE5YjMxYjg0YTRmNGQwZTYyNzAwYWUwOTQyMDRjOWRhYmVlMTcyNDRiNjI5MjZqLHBsbW50MTk5emYwdmttZWhocjJoaGR0M2U0MjVyNWR4NDc0OWRtZW5tMzV3EmIKTgpGCh8vY29zbW9zLmNyeXB0by5zZWNwMjU2azEuUHViS2V5EiMKIQLrk8HpZN1Y2GEZO/AVsHQ4HUQyKCGnnFSiC0VbTFfBxhIECgIIARIQCgoKBXBsbW50EgExEMCaDBpARkw+0nSaage+6g7wSsY4wdUanxG8pfjs51x5yLzulDRuBKJkUo8+zRFEvijctPBsXVx0wYzxZEsJgw9TMVUdUQ=="
    machine_id = "6003d0ab9af4ec112629195a7266a244aecf1ac7691da0084be3e7ceea2ee71571b0963fffd9c80a640317509a681ac66c2ed70ecc9f317a0d2b1a9bff94ff74"
    signature = "022100e51cf02a0b900a36f78e8c1ff0562879469094e42ab44db137297c686a1d928e022100b84583ceda145d10d019b31b84a4f4d0e62700ae094204c9dabee17244b62926"

    issuerLiquid = "pmpb7vUTeBGCD5Jtz9zrrcqWoMBXdQVEr1qebJsYgETXNebuKmnzMi4S2bMqpEswLUmEa2s6HeXz8cgVrdsYTnQVtcxbd5Vr7ZZpqmMGX6ZT8tQ"
    issuerPlanetmint = "xpub6GhJtmsZ5T6zFPB961YVSpMEkoGQ2McYE53HQDiqYx5bYwiCmgAhewVJSCVkh38oVeHtaAV9QJJ1aSEJZszj14e8G83ZL3CVS5bdDqu3nWn"
    gps = '{"Latitude":"-48.876667","Longitude":"-123.393333"}'
    deviceDefinition = '{"Manufacturer": "RDDL","Serial":"AdnT2uyt"}'

    PlanetmintKeys = trust_wallet.get_planetmint_keys()
    address = PlanetmintKeys.planetmint_address
    issuerPlanetmint = PlanetmintKeys.extended_planetmint_pubkey
    issuerLiquid = PlanetmintKeys.extended_liquid_pubkey
    # process TA input to be plmnt compatible
    signature = "30" + hex(int(len(signature) / 2))[2:] + signature
    PlanetmintKeys = trust_wallet.get_planetmint_keys()

    assert address == "plmnt199zf0vkmehhr2hhdt3e425r5dx4749dmenm35w"
    # assert issuerPlanetmint == "xpub6GhJtmsZ5T6zFPB961YVSpMEkoGQ2McYE53HQDiqYx5bYwiCmgAhewVJSCVkh38oVeHtaAV9QJJ1aSEJZszj14e8G83ZL3CVS5bdDqu3nWn"
    # assert issuerLiquid == "pmpb7vUTeBGCD5Jtz9zrrcqWoMBXdQVEr1qebJsYgETXNebuKmnzMi4S2bMqpEswLUmEa2s6HeXz8cgVrdsYTnQVtcxbd5Vr7ZZpqmMGX6ZT8tQ"
    assert (
        machine_id
        == "6003d0ab9af4ec112629195a7266a244aecf1ac7691da0084be3e7ceea2ee71571b0963fffd9c80a640317509a681ac66c2ed70ecc9f317a0d2b1a9bff94ff74"
    )
    assert binascii.unhexlify(PlanetmintKeys.raw_planetmint_pubkey) == bytes(reference_pub_key)
    assert (
        "3046022100e51cf02a0b900a36f78e8c1ff0562879469094e42ab44db137297c686a1d928e022100b84583ceda145d10d019b31b84a4f4d0e62700ae094204c9dabee17244b62926"
        == signature
    )
    # accountID, sequence, statusText = getAccountInfo("http://localhost:1317", PlanetmintKeys.planetmint_address)
    # assert "" == statusText # on failure: account does not yet exist on chain

    issuerPlanetmint = "xpub6GhJtmsZ5T6zFPB961YVSpMEkoGQ2McYE53HQDiqYx5bYwiCmgAhewVJSCVkh38oVeHtaAV9QJJ1aSEJZszj14e8G83ZL3CVS5bdDqu3nWn"
    issuerLiquid = "pmpb7vUTeBGCD5Jtz9zrrcqWoMBXdQVEr1qebJsYgETXNebuKmnzMi4S2bMqpEswLUmEa2s6HeXz8cgVrdsYTnQVtcxbd5Vr7ZZpqmMGX6ZT8tQ"
    sequence = 0
    accountID = 15
    tx = attestMachine(
        address,
        "MyMachine0",
        issuerPlanetmint,
        issuerLiquid,
        gps,
        deviceDefinition,
        machine_id,
        signature,
        "",
        "planetmintgo",
        accountID,
        sequence,
    )
    assert expected_result == tx


def test_notarize_asset_valid():
    trust_wallet = TrustWalletConnector("/dev/ttyACM0")
    recoverPhrase = "penalty police pool orphan snack faith educate syrup skill picnic prepare mystery dune control near nation report evolve ethics genius elite tool rigid crane"
    result = trust_wallet.recover_from_mnemonic(recoverPhrase)
    assert recoverPhrase == result

    PlanetmintKeys = trust_wallet.get_planetmint_keys()
    accountID, sequence, statusText = getAccountInfo("http://localhost:1317", PlanetmintKeys.planetmint_address)
    assert "" == statusText  # on failure: account does not yet exist on chain

    tx = notarizeAsset("cid", "planetmintgo", accountID, sequence)
    assert (
        "Cl0KWwokL3BsYW5ldG1pbnRnby5hc3NldC5Nc2dOb3Rhcml6ZUFzc2V0EjMKLHBsbW50MTk5emYwdmttZWhocjJoaGR0M2U0MjVyNWR4NDc0OWRtZW5tMzV3EgNjaWQSZApQCkYKHy9jb3Ntb3MuY3J5cHRvLnNlY3AyNTZrMS5QdWJLZXkSIwohAuuTwelk3VjYYRk78BWwdDgdRDIoIaecVKILRVtMV8HGEgQKAggBGAISEAoKCgVwbG1udBIBMRDAmgwaQMWakNURssQsAKf3eDUGr29/WUbN1gLRFhoDfSflSdMfbTSVb9YaxXBlnS6ElLwuh7Qc/xB3+K2OmdomyMW1EFE="
        == tx
    )
