from app.RddlInteraction.planetmint_interaction import createAccountOnNetwork, getAccountInfo, attestMachine
from app.RddlInteraction.TrustWallet.occ_messages import TrustWalletInteraction


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


def test_attestMachine_valid():
    machine_id = "6003d0ab9af4ec112629195a7266a244aecf1ac7691da0084be3e7ceea2ee71571b0963fffd9c80a640317509a681ac66c2ed70ecc9f317a0d2b1a9bff94ff74"
    address = "plmnt196ucf7y7t6x7kuvzlx5rpju5822efjelmn7xz0"
    signature = "022100e51cf02a0b900a36f78e8c1ff0562879469094e42ab44db137297c686a1d928e022100b84583ceda145d10d019b31b84a4f4d0e62700ae094204c9dabee17244b62926"

    issuerLiquid = "pmpb7vUTeBGCD5Jtz9zrrcqWoMBXdQVEr1qebJsYgETXNebuKmnzMi4S2bMqpEswLUmEa2s6HeXz8cgVrdsYTnQVtcxbd5Vr7ZZpqmMGX6ZT8tQ"
    issuerPlanetmint = "xpub6GhJtmsZ5T6zFPB961YVSpMEkoGQ2McYE53HQDiqYx5bYwiCmgAhewVJSCVkh38oVeHtaAV9QJJ1aSEJZszj14e8G83ZL3CVS5bdDqu3nWn"
    gps = '{"Latitude":"-48.876667","Longitude":"-123.393333"}'
    deviceDefinition = '{"Manufacturer": "RDDL","Serial":"AdnT2uyt"}'
    # process TA input to be plmnt compatible
    signature = "30" + hex(int(len(signature) / 2))[2:] + signature
    trust_wallet = TrustWalletInteraction("/dev/ttyACM0")
    PlanetmintKeys = trust_wallet.get_planetmint_keys()
    accountID, sequence, statusText = getAccountInfo("http://localhost:1317", PlanetmintKeys.planetmint_address)
    assert "" == statusText
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
    print(tx)
