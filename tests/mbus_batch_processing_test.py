import pytest
import re
from app.energy_agent.smart_meter_reader.mbus_reader import MbusReader
from app.energy_agent.smart_meter_reader.mbus_frame import DLMSFrame

#batches = [
#    {  "batches": "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e955d38b5d2fbbb883f65c43ee926dbb636bc9af9025ace1d73291a2bcbee409b793074a824e5ff63bd70b79ac46d6f98d09a86acb7e2af1f1cde84f1e139dd36f3c91d1f0ad9057225ddb5cb430647e",
#       "encryptionkey":  "4475D2230289243A4AE7732E2396C572"
#        "authkey": "8FEADE1D7057D94D816A41E09D17CB58"
#    },
#    {  "batches": "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e955d38b5d2fbbb883f65c43ee926dbb636bc9af9025ace1d73291a2bcbee409b793074a824e5ff63bd70b79ac46d6f98d09a86acb7e2af1f1cde84f1e139dd36f3c91d1f0ad9057225ddb5cb430647e",
#       "encryptionkey":  "4475D2230289243A4AE7732E2396C572"
#        "authkey": "8FEADE1D7057D94D816A41E09D17CB58"
#    },
#    
#
#]


frames = [
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb901270657e",
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8cacbb3176bfb6d62b4340d8f1faed60d316317766f277899e0f285282779d1acf4b02960dd76d66210a77bddfb19338ce2ca4f41a083737cefc2d0134b3a5194c2656cc2647be83a21acaf1c17287e",
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8caca3a52a875c7500f842da0ca6ac1d98c0abbf61ed49e3d6eb3d4ff133324b53371759b9a470b0ce2c1efeb8c20179cdb68b14b7bd6540cb596c91382e18b88bc04ecdc3104dadaeb5dbfa074cb7e",
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8cac64953ac1f7aa3185c28b0642bd7bdf041628d27348f232b39484030207c9a272f68945a771960d72c2bef6d22660416c9e05436aecaa6167fe63b85473505cd4bfaadb477fd120be1ef9552d97e",
    "7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7e8e820103300009833108abce90b04deb2c46f68ae7d8e04f42404131bb25d50be0de4b6c81c6bcb7f094c2f9cf41f85dae692eefd67d74a1c12045fc673e72143da1ea280d7b38751e33a38af80d5b641c2b9025dfa64d2ad115064af080086a141563f5056caf7b3a99595f904ef3527e",
    "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e87ea30fed7047d500c157a153258f4101eb0a5b892f58f62805ce0873f696990b95df9c45f40e3845d5e279cc33073504285e5d98a1c24a3efdf066cf1f1420f5da462b6410ebbd7896daad93a9d87e",
    "7ea08bceff0313eee1e6e700e0400001000077db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d420ae57e"\
    "7ea08bceff0313eee1e040000200007a474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b80307197e"\
    "7ea08bceff0313eee1e040000300007a68e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893a5257e"\
    "7ea078ceff03138463e0c00004000067a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315dd0d7e",
    ]

def test_parse_frames():
    for frame in frames:
        byte_frame = bytearray.fromhex(frame)
        extracted_frames = MbusReader.extract_frames(bytearray.fromhex(frame))
        for ext_frame in extracted_frames:
            dlms_frame = DLMSFrame(ext_frame)
            assert len(ext_frame) -2 == dlms_frame.length 
            print(dlms_frame.get_payload_hex())
            
    assert False

def test_read_frames():
    for frame in frames:
        print(f"frame: {frame}")
        extracted_frames = MbusReader.extract_frames(bytearray.fromhex(frame))
        if frames[6] == frame:
            assert len(extracted_frames) == 4
            index = 0
            for ext_frame in extracted_frames:
                print(f"ext frame {ext_frame.hex()}")
                data = MbusReader.extract_data_from_frame(ext_frame)
                if index == 0:
                    assert data != None
                    assert len(data) == 121
                else:
                    assert data == None
                index = index +1

        else:
            assert len(extracted_frames) == 1
            assert extracted_frames[0].hex() == frame
            data = MbusReader.extract_data_from_frame(extracted_frames[0])
            assert data != None
            if frames[4] == frame:
                assert len(data) == 121
            else:
                assert len(data) == 92
        
        
        