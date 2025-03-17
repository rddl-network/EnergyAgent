import json
import pytest
from app.energy_agent.smart_meter_reader.mbus_reader import MbusReader
from app.energy_agent.smart_meter_reader.mbus_frame import DLMSFrame
from app.energy_agent.smart_meter_reader.dlms_parser import DSMRParser
from app.energy_agent.smart_meter_reader.lg_e450 import parse_e450_meter_data

from app.energy_agent.energy_decrypter import (
    decrypt_aes_gcm_landis_and_gyr,
    decrypt_gcm,
    unwrap_apdu,
    decrypt_evn_data,
    parse_dsmr_frame,
    unwrap_gxdlm,
)


@pytest.mark.skip(reason="unable to parse this payload workshop meter")
def test_decrypt_payload():
    dec_key_bytes = bytes.fromhex("4475D2230289243A4AE7732E2396C572")
    auth_key_bytes = bytes.fromhex("8FEADE1D7057D94D816A41E09D17CB58")

    payload = "db084c475a6773745ddd4f2000e98dfa5b3752103b634363c4ed54f3d21f13c6174c786adbaaf3c763d9a7f09e8d5c9461854bf50a8417f5dd779104c3ae7f1cb43f8408036e32ef34afe27eb1ac03f2cdb3de617811baeb7302"

    obis_dlms = decrypt_gcm(auth_key_bytes, payload, dec_key_bytes)
    print(obis_dlms)
    data = parse_e450_meter_data(obis_dlms)
    data_str = json.dumps(data, indent=2)
    assert data["frame_info"]["frame_valid"]

    payload = "db084c475a6773745ddd4f2000e98779aba887d3fbd6d2227dec5bd8f2c8e144071505032adb39a939db833bc5d34d5e2987af79c95f3adfcd9efacfde55c3ce74b1d66f1d03519d12e524b4db61db2d0894a154dfb310712d4f"
    obis_dlms = decrypt_gcm(auth_key_bytes, payload, dec_key_bytes)
    print(obis_dlms)
    data = parse_e450_meter_data(obis_dlms)
    data_str = json.dumps(data, indent=2)

    assert data["frame_info"]["frame_valid"]


def test_decrypt_payload_0000():
    dec_key_bytes = bytes.fromhex("00000000000000000000000000000000")
    auth_key_bytes = bytes.fromhex("00000000000000000000000000000000")
    frame = "db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d420a474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b8030768e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893a5a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315dd"
    print(f"Type of authentication_key: {type(auth_key_bytes)}")
    obis_dlms = decrypt_gcm(auth_key_bytes, frame, dec_key_bytes)
    data = parse_e450_meter_data(obis_dlms)

    data_str = json.dumps(data, indent=2)
    assert type(data_str) == str
    assert data["frame_info"]["frame_valid"]


def test_obis_decoder_lg_e450():
    obis_dlms = "0f00b1ce270c07e70a0c040e0528ff80000002120112020412002809060008190900ff0f02120000020412002809060008190900ff0f01120000020412000109060000600100ff0f02120000020412000809060000010000ff0f02120000020412000309064c0b7ca80cbbadc4b1061f912b63ee54b092ba19f428024561235a514f6410e6500c47e4b477f93f4a32b3afaec87c3d5efb79aae0b7b3e125736f124eeb1d8a70eb10c3319916d247f783a1b7cd760399025e057ebd96caa6ac601b56ab15eaf55f560dd4ffa781d94e2d327c2e2682fbbb4bf3ee37e27b2da96be3038f6c1e4e601ca21e7762dfe8bfd845f3578faf98f1f5e669001d9ac77f329465146c55c842e0f06ed0c28614f55141d4f431991ea27622544865e9aaf28424ad506dd6757a538dc655b51d8b922f49b7303f5cc235bf01c06125f29921877a145975e25adf43823afc4daeba6db17518ed8a6d3aca1e07d85c5fbd7e777b9eaa49e7e7a2b6ab7c617f94bcba7d5971d4015eed62b3375eb04f5e7f1d95e7b5ca224a26ea3beb540c3d249928af4d3c0569c1d7498d905808e1fc6aeec8402b92c5d2cccabdc1c483ff5e87fb53109353a9995ea94eef"
    data = parse_e450_meter_data(obis_dlms)

    data_str = json.dumps(data, indent=2)
    assert type(data_str) == str


def test_obis_decoder_lg_e450_49928Wh():
    obis_dlms = "0f00befa6e0c07e70c01050c0d05ff80000002120112020412002809060008190900ff0f02120000020412002809060008190900ff0f01120000020412000109060000600100ff0f02120000020412000809060000010000ff0f02120000020412000309060100010700ff0f02120000020412000309060100020700ff0f02120000020412000309060100010800ff0f02120000020412000309060100020800ff0f02120000020412000309060100030700ff0f02120000020412000309060100040700ff0f02120000020412000309060100030800ff0f02120000020412000309060100040800ff0f021200000204120003090601001f0700ff0f02120000020412000309060100330700ff0f02120000020412000309060100470700ff0f02120000020412000309060100200700ff0f02120000020412000309060100340700ff0f02120000020412000309060100480700ff0f0212000009060008190900ff09083536383135393330090c07e70c01050c0d05ff80000106000000080600000000060000c3080600000000060000000006000000070600001259060000e39b1200081200001200001200ed120000120000"
    data = parse_e450_meter_data(obis_dlms)
    assert data["potential_energy_values"][7]["position"] == 388
    assert data["potential_energy_values"][7]["value"] == 49.928
    assert data["obis_values"]["1.0.1.8.0.255"]["interpretation"] == "Active energy + (Wh) total"
    # obis_dlms_parsed["obis_values"][5]["interpretation"]
    data_str = json.dumps(data, indent=2)
    assert type(data_str) == str
