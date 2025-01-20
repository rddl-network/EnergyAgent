import pytest
from app.energy_agent.smart_meter_reader.mbus_reader import MbusReader
from app.energy_agent.smart_meter_reader.mbus_frame import DLMSFrame
from app.energy_agent.smart_meter_reader.dlms_parser import DSMRParser


from app.energy_agent.energy_decrypter import decrypt_aes_gcm_landis_and_gyr, decrypt_gcm, unwrap_apdu, decrypt_evn_data
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


frames_data = [
    {
        "frame_id": 1,
        "frame": "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb901270657e",
        "length": [90],
        "num_frames": 1,
        "data": ["db084c475a6773745ddd4f2000e8c3f44d3b65fcf023f403e19036a1c9f5e6eabdf04c40a4800b1509a2252881267d0b90e585eef07f57c90ad75192893725ae5f06bacee5a422d33f1705a1919765812e06910abfdb2beb9012"],
    },
    {
        "frame_id": 2,
        "frame": "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8cacbb3176bfb6d62b4340d8f1faed60d316317766f277899e0f285282779d1acf4b02960dd76d66210a77bddfb19338ce2ca4f41a083737cefc2d0134b3a5194c2656cc2647be83a21acaf1c17287e",
        "length": [90],
        "num_frames": 1,
        "data": ["db084c475a6773745ddd4f2000e8cacbb3176bfb6d62b4340d8f1faed60d316317766f277899e0f285282779d1acf4b02960dd76d66210a77bddfb19338ce2ca4f41a083737cefc2d0134b3a5194c2656cc2647be83a21acaf1c"],
    },
    {
        "frame_id": 3,
        "frame": "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8caca3a52a875c7500f842da0ca6ac1d98c0abbf61ed49e3d6eb3d4ff133324b53371759b9a470b0ce2c1efeb8c20179cdb68b14b7bd6540cb596c91382e18b88bc04ecdc3104dadaeb5dbfa074cb7e",
        "length": [90],
        "num_frames": 1,
        "data": ["db084c475a6773745ddd4f2000e8caca3a52a875c7500f842da0ca6ac1d98c0abbf61ed49e3d6eb3d4ff133324b53371759b9a470b0ce2c1efeb8c20179cdb68b14b7bd6540cb596c91382e18b88bc04ecdc3104dadaeb5dbfa0"],
    },
    {
        "frame_id": 4,
        "frame": "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e8cac64953ac1f7aa3185c28b0642bd7bdf041628d27348f232b39484030207c9a272f68945a771960d72c2bef6d22660416c9e05436aecaa6167fe63b85473505cd4bfaadb477fd120be1ef9552d97e",
        "length": [90],
        "num_frames": 1,
        "data": ["db084c475a6773745ddd4f2000e8cac64953ac1f7aa3185c28b0642bd7bdf041628d27348f232b39484030207c9a272f68945a771960d72c2bef6d22660416c9e05436aecaa6167fe63b85473505cd4bfaadb477fd120be1ef95"],
    },
    {
        "frame_id": 5,
        "frame": "7ea08bceff0313eee1e6e700e0400001000077db084c475a67737c7e8e820103300009833108abce90b04deb2c46f68ae7d8e04f42404131bb25d50be0de4b6c81c6bcb7f094c2f9cf41f85dae692eefd67d74a1c12045fc673e72143da1ea280d7b38751e33a38af80d5b641c2b9025dfa64d2ad115064af080086a141563f5056caf7b3a99595f904ef3527e",
        "length": [119],
        "num_frames": 1,
        "data": ["db084c475a67737c7e8e820103300009833108abce90b04deb2c46f68ae7d8e04f42404131bb25d50be0de4b6c81c6bcb7f094c2f9cf41f85dae692eefd67d74a1c12045fc673e72143da1ea280d7b38751e33a38af80d5b641c2b9025dfa64d2ad115064af080086a141563f5056caf7b3a99595f904e"],
    },
    {
        "frame_id": 6,
        "frame": "7ea067ceff031338bde6e700db084c475a6773745ddd4f2000e87ea30fed7047d500c157a153258f4101eb0a5b892f58f62805ce0873f696990b95df9c45f40e3845d5e279cc33073504285e5d98a1c24a3efdf066cf1f1420f5da462b6410ebbd7896daad93a9d87e",
        "length": [90],
        "num_frames": 1,
        "data": ["db084c475a6773745ddd4f2000e87ea30fed7047d500c157a153258f4101eb0a5b892f58f62805ce0873f696990b95df9c45f40e3845d5e279cc33073504285e5d98a1c24a3efdf066cf1f1420f5da462b6410ebbd7896daad93"],
    },
    {
        "frame_id": 7,
        "frame": "7ea08bceff0313eee1e6e700e0400001000077db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d420ae57e"\
                 "7ea08bceff0313eee1e040000200007a474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b80307197e"\
                 "7ea08bceff0313eee1e040000300007a68e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893a5257e"\
                 "7ea078ceff03138463e0c00004000067a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315dd0d7e",
        "length": [119,122,122,103],
        "num_frames": 4,
        "data": ["db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d42",
                 "474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b803",
                 "68e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893",
                 "a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315"],
    }
]


multi_frames = [
    { 
        "frame": "7ea08bceff0313eee1e6e700e0400001000077db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d420ae57e"\
                 "7ea08bceff0313eee1e040000200007a474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b80307197e"\
                 "7ea08bceff0313eee1e040000300007a68e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893a5257e"\
                 "7ea078ceff03138463e0c00004000067a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315dd0d7e",
        "encryption_key" : "00000000000000000000000000000000",
        "auth_key" : "00000000000000000000000000000000",
        "payload": "db084c475a677362f13a8201c53000b1cdb52ec1eb626fde9e6d337047190e0cb1ca7f6d681d0dbede752c685dadf86382cf4ea66bb1890e11fdb1eb87090db5fc451603362da0ce529e57cb0be9e3af314e61ef3c3ea7ec236dcc3846bacd3256c98a220165fcc30696c7a8a3b44114b87c816b760d42474c319e92d674b21117089bb4c52b7cc551eaf3052a2892fcdd95c48bedf90d5d521cfe4b3cc4f3b974c865d9116d5208e19831d869db3a1d6609e4a54c43c9b9504495a43e21f5b344c462d5e79e9f1416484f359a0cc56ac0a1bae8445144bee3a7aa7e8320b36a2703374a6441cb307430c13d0ae891b80368e7626e0f7045185945483038efd0520c05ff5179f8e0090ae86317718fa4f09666f7609b365a72bb82e655242c3fdb7c9aa86c9de78346fc62a92a8bc421c9aaef15bf786b09035a8d95de21c38a56a5e01dd2308ef2b949aa89c8a53c3d1d8e609ac6e026a8f9eb79d597983a2b519b24cbce415c74947893a0c6fc1db0926f2ec72fc115bb4f8ff217c356a2752c1c0ef4195e1c5312ab0d23e2535cffc6bd4a0c9f002c753b05ac313888a81021e52c248cebf3c566639b6e82755d6abd1da2b4ca707812cdb9c44e4688c957c9d9c488705d0e098b41d6096d259ebde315",
        "apdu": "0f00b1ce270c07e70a0c040e0528ff80000002120112020412002809060008190900ff0f02120000020412002809060008190900ff0f01120000020412000109060000600100ff0f02120000020412000809060000010000ff0f02120000020412000309060100010700ff0f02120000020412000309060100020700ff0f02120000020412000309060100010800ff0f02120000020412000309060100020800ff0f02120000020412000309060100030700ff0f02120000020412000309060100040700ff0f02120000020412000309060100030800ff0f02120000020412000309060100040800ff0f021200000204120003090601001f0700ff0f02120000020412000309060100330700ff0f02120000020412000309060100470700ff0f02120000020412000309060100200700ff0f02120000020412000309060100340700ff0f02120000020412000309060100480700ff0f0212000009060008190900ff09083536383135393330090c07e70a0c040e0528ff80008106000000000600000000060000c28d0600000000060000000006000000000600001259060000e39b1200001200001200001200ea120000120000",
        "unwrapped_apdu": """XML Content:
<DataNotification>
  <LongInvokeIdAndPriority Value="00B1CE27" />
  <DateTime Value="07E70A0C040E0528FF800000" />
  <NotificationBody>
    <DataValue>
      <Structure Qty="12">
        <Array Qty="12">
          <Structure Qty="04">
            <UInt16 Value="0028" />
            <OctetString Value="0008190900FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0028" />
            <OctetString Value="0008190900FF" />
            <Int8 Value="01" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0001" />
            <OctetString Value="0000600100FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0008" />
            <OctetString Value="0000010000FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100010700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100020700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100010800FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100020800FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100030700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100040700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100030800FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100040800FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="01001F0700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100330700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100470700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100200700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100340700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
          <Structure Qty="04">
            <UInt16 Value="0003" />
            <OctetString Value="0100480700FF" />
            <Int8 Value="02" />
            <UInt16 Value="0000" />
          </Structure>
        </Array>
        <OctetString Value="0008190900FF" />
        <OctetString Value="3536383135393330" />
        <OctetString Value="07E70A0C040E0528FF800081" />
        <UInt32 Value="00000000" />
        <UInt32 Value="00000000" />
        <UInt32 Value="0000C28D" />
        <UInt32 Value="00000000" />
        <UInt32 Value="00000000" />
        <UInt32 Value="00000000" />
        <UInt32 Value="00001259" />
        <UInt32 Value="0000E39B" />
        <UInt16 Value="0000" />
        <UInt16 Value="0000" />
        <UInt16 Value="0000" />
        <UInt16 Value="00EA" />
        <UInt16 Value="0000" />
        <UInt16 Value="0000" />
      </Structure>
    </DataValue>
  </NotificationBody>
</DataNotification>"""
    }                 

]
def test_multi_frame():


    for multi_frame in multi_frames:
        dec_key_bytes = bytes.fromhex(multi_frame["encryption_key"]),
        auth_key_bytes = bytes.fromhex(multi_frame["auth_key"]),
        extracted_frames = MbusReader.extract_frames(bytearray.fromhex(multi_frame["frame"]))
        total_payload = bytearray()
        for ext_frame in extracted_frames:
            dlms_frame = DLMSFrame(ext_frame)
            assert len(ext_frame) -2 == dlms_frame.length 
            total_payload.extend(dlms_frame.get_payload())
        print( f"total payload: {total_payload.hex()}")
        assert multi_frame["payload"] == total_payload.hex()
        
        apdu = decrypt_gcm(auth_key_bytes[0], total_payload.hex(), dec_key_bytes[0])
        print(f"apdu: {apdu}")
        assert multi_frame["apdu"] == apdu
        # unwrapped = unwrap_apdu(apdu)
        # print(unwrapped)
        # assert multi_frame["unwrapped_apdu"] == unwrapped

@pytest.mark.skip(reason="unable to parse this payload workshop meter")
def test_decrypt_payload():
    dec_key_bytes =  bytes.fromhex("4475D2230289243A4AE7732E2396C572")
    auth_key_bytes = bytes.fromhex("8FEADE1D7057D94D816A41E09D17CB58")
    
    payload = "db084c475a6773745ddd4f2000e98779aba887d3fbd6d2227dec5bd8f2c8e144071505032adb39a939db833bc5d34d5e2987af79c95f3adfcd9efacfde55c3ce74b1d66f1d03519d12e524b4db61db2d0894a154dfb310712d4f"
    payload = "db084c475a6773745ddd4f2000e98dfa5b3752103b634363c4ed54f3d21f13c6174c786adbaaf3c763d9a7f09e8d5c9461854bf50a8417f5dd779104c3ae7f1cb43f8408036e32ef34afe27eb1ac03f2cdb3de617811baeb7302"
    
    assert False

@pytest.mark.skip(reason="CRC computation does not work right now")
def test_parse_frames():
    for frame in frames:
        extracted_frames = MbusReader.extract_frames(bytearray.fromhex(frame))
        for ext_frame in extracted_frames:
            dlms_frame = DLMSFrame(ext_frame)
            assert len(ext_frame) -2 == dlms_frame.length 
            print(dlms_frame.get_payload_hex())
            assert dlms_frame.verify_checksum()
    assert False



def test_read_frames():
    for frame_data in frames_data:
        print(f"frame: {frame_data}")
        extracted_frames = MbusReader.extract_frames(bytearray.fromhex(frame_data["frame"]))

        assert frame_data["num_frames"] == len(extracted_frames)
        index = 0
        for ext_frame in extracted_frames:
            print(f"ext frame {ext_frame.hex()}")
            dlms_frame = DLMSFrame(ext_frame)
            assert len(ext_frame) -2 == dlms_frame.length 
            data = dlms_frame.get_payload()
            assert data != None
            assert frame_data["length"][index] == len(data)
            assert frame_data["data"][index] == data.hex()
            index = index +1
     
        