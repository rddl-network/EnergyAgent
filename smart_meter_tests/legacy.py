""" To decorde smart meter data retrieved from the infra red customer interface provided by Wiener Netze. Tested with Iskra AM550 (But should work for all smart meters provided by Wiener Netze) """

# you might need to install pycryptodome
from datetime import datetime
from hashlib import sha256

import ecdsa

selection = "Matthias"
verify_signature = False


if selection == "Matthias":
    key_smart_meter = "62DC84B413AF3E16AA271CE9ED04AC74"  # Matthias
    payload = "7ea067cf022313fbf1e6e700db0849534b6974a8d8994f2000909dd750e337f09d460befa73f43e61e5cbdd88f7f1e4a91ff2fcb38b8fd4e38bd0d431f6f42892c24545b49389a5b4a3e976c924ae466d4e25abfd26a1573b95c0a4a4bce9a273f1233765c38da4c76779c3821aa9243d34209e33e1bf67a9eee813f0773308227d34232eb863933b3cf9c8aa58966ffeb0a2ade0add0b1b35147be913ddd3e22f1045a33d8bd72345ec83f784e3086b0810b7b344cba4a6a0f9aa37d5f5c1e092b1ef198ae08dae"  # Matthias home unsliced
    public_key_byte_string = "041D1F36BB2C5362B8BE3AD472084AC3623F4B8F4890BAFECAD0EC7CFF53AA45412C1A67F29121028AA841E344E7A77D124993EDEF3A84C9A252F7C5E7A6A10B94"  # public key in byte (remove first byte 04 as it just a notation)
    data = payload[
        :210
    ]  # sclice the data from the smart meter (missing byte. that's the reasion why not payload[:(-128-64)]) only 104bytes are sent instead of the original 105bytes.
elif selection == 0:  # rpi-zero0 - SIEMENS
    key_smart_meter = "4F9278B252D90B3F742F5711232AD27A"  # SMS1030788000020
    payload = "7ea07bcf000200231362b1e6e700db08534d5367753ec614612000124ef6b993602ba8f1abb3c5d7208604f922f1240720e5d60b3846a3c9bcce2fbed4c9f87da01a2fd084fb0d1846b4b299326db5524b4d0fc60adbaf8af60fbbcca86fe755b6223c787d23d0466f93d4c5ee906692cc2fb77e61f60f5a2ad44f777eb88ad7d2ed2cc4a09072c98423ab030fbbf70d9b7881da9fba8ca3e30875d016675837c40aa962359593401300deae193655e3bb6fa46ab2d54adabaabb939e783f95489289c8b00b38dad308a41327320650ec9cb5de0296861ca05ae84bc2f"  # rpi-zero0
    public_key_byte_string = "04cf711f82714be5ec70f17f35c77a57a735f30d48914d7a479b77427922a9eacb17215d6a895bbbbe09ee109d83b079a39ae0b285e8a23b5487c5b944bc19cc7f"
    data = payload[: (-128 - 64)]
# elif selection == 1: # rpi-zero1 # SMART ENERGY READER NOT WORKING
#     key_smart_meter = ""
#     payload = ""
#     public_key_byte_string = ""
#     data=payload[:(-128-64)]
elif selection == 2:  # rpi-zero2 - ISKRA
    key_smart_meter = "927CE4ECA62FE23E19406C5EE452285E"  # ISK1050771045183
    payload = "7ea067cf022313fbf1e6e700db0849534b69743c103f4f200010d9e208f5c0c61a10c2359a014dfa00024e52839d213a16b086e297ad13f7db4574d0d4d3aff9bada8f10f3bb33a39ac2fc5fb447342ff4d6a9e9361ecbd84c9b6f76f5ece94425b2917a660b0af27e41fd07ddf650be01e89564063f58a8800c401c894d1bcfcfa5bac541fc79c302ab606511dee0eca4fc15d72b24314c9265bc4c9295f2e619419f9c082e025d52cac968fec6aff04774018dda4e614d71284fe3ffe439c2eaf550e38cb621e0c1"  # rpi-zero2
    # payload='7ea067cf022313fbf1e6e700db0849534b69743c103f4f200013d70f74af724ce295f92cd7dc13e8391bf93bcf7bc32d8e502ce9a1031c19687b331fa039afcc43ceb62ef4217330a0788d791c617e713f21383f88ec11f9086687739d451fc804b3a40ce1c902ad7eb774633274d81cec41b6408a68968bce5bd96df98fb5fd6e6c46c638771a2a696fb7a9cf8372115c08bf1b544856eb6fb74f7c2033748b78bdc172b3e4d98e22d426b430ca030c126951eb75131bf458c4673f18b058dff2f54332a149e655c4'
    public_key_byte_string = "044d7bd8e2c066adeaf3bc41446e5908e876d2ac8b694c8d482e15a2760d5ef194a198e5d062fffaea8a5a407da40ad81423ab4c97cb1fb0b2f55c41f68e91f2ce"
    data = payload[: (-128 - 64)]
elif selection == 3:  # rpi-zero3 - LANDIS+GYR
    key_smart_meter = "1F51C774301C3E940065D9200DDDA5B4"  # LGZ1030740710430
    payload = "7ea067ceff031338bde6e700db084c475a67726d311e4f200021ed98f64d452292bf5966b5af37da66b67a4a49f9186244b1aa594e80248e44b9ce93cf04c54d209880fffa632a60c474591763cc1d31803012531dc84f1b43e0e4d076b57fb8f4cdef1f86f36d497e4d97b172f3ce2c63306f1ca35c9e60ed4f00ef841e98b2012446a165a0aa8a1eb324786889cd85a62bb09615da71f3f13d8b81b22232aea015b3d0adea0465aa2e32492b8197ddbc84f7d79b0ce78c65650825218cd15f70b60942e3e7837b68"
    public_key_byte_string = "04f559f84b07d58575761e0fc3bdbcf8fc46d17c2f237e0cffd998062ff64b57fbe597ef9945478dfab072d398cfea2ff92ce0c85b957c89e3888b71e86612d187"
    data = payload[: (-128 - 64)]
elif selection == 4:  # rpi-zero9 - LANDIS+GYR Klagenfurt Stadtwerke
    key_smart_meter = "00000000000000000000000000000000"  # LGZ1030740710430
    payload = "fqCLzv8DE+7h5ucA4EAAAQAAd9sITEdaZ3Ni8TqCAcUwAB195l9hkuBqMoS6RZ+8FNo1o0U5n+wsM3MOWRi1RQcS1dtsukmxSDdOrk1sEmwukiDRYoyR27rhGxCQIs2AL4nvg+2qlnnn+nsM1POQSovYWoFzbtsKAEGVDULSlReOOw/4VCov+4WSflt+zwTBTxzXDlKfQXWo/7ETqxAxEPy1Ay7WoLy5gm6fjkwmXHVAJ2UxbKHUU7Y0uqXtY37l64xoPz2b7rPKfd/9Hy5BkkCxYXxaWEiRUCOPOnW/i5fV7SG8ElKHMT0S4rM9"
    public_key_byte_string = "04f559f84b07d58575761e0fc3bdbcf8fc46d17c2f237e0cffd998062ff64b57fbe597ef9945478dfab072d398cfea2ff92ce0c85b957c89e3888b71e86612d187"
    data = payload[: (-128 - 64)]


signature = payload[-128:]
digest = payload[(-128 - 64) : -128]

if verify_signature:
    vk = ecdsa.VerifyingKey.from_string(
        bytes.fromhex(public_key_byte_string[2:]), curve=ecdsa.NIST256p, hashfunc=sha256
    )  # the default is sha1

    # valid_signature = vk.verify_digest(bytes.fromhex(signature), bytes.fromhex(digest)) # you can verify directly the hash
    valid_signature = vk.verify(
        bytes.fromhex(signature), bytes.fromhex(data)
    )  # or you can directly use the data, might of use if we decide to get rid of the hash

    print(f"The signature of the data is: {valid_signature}")

device = "WN"

# data='7ea067cf022313fbf1e6e700db0844556677889900aa4f20888877775540d5496ab897685e9b7e469942209b881fe280526f77c9d1dee763afb463a9bbe88449cb3fe79725875de945a405cb0f3119d3e06e3c4790130a29bc090cdf4b323cd7019d628ca255fce57e' # example
# data string of WienerNetze explained:
# 7e         start-byte, hdlc opening flag
# a0         address field?
# 67         length field?
# cf         control field?
# 02         length field?
# 23         ?
# 13         frame type
# fbf1       crc16 from byte 2-7
# e6e700     some header?
# db         some header?
# 08         length of next field
# 44556677889900aa   systemTitle
# 4f         length of next field
# 20         security byte: encryption-only
# 88887777   invocation counter
# 5540d5496ab897685e9b7e469942209b881fe280526f77c9d1dee763afb463a9bbe88449cb3fe79725875de945a405cb0f3119d3e06e3c4790130a29bc090cdf4b323cd7019d628ca255 ciphertext
# fce5       crc16 from byte 2 until end of ciphertext
# 7e         end-byte

## lets go
import binascii

##CRC-STUFF BEGIN
CRC_INIT = 0xFFFF
POLYNOMIAL = 0x1021


def byte_mirror(c):
    c = (c & 0xF0) >> 4 | (c & 0x0F) << 4
    c = (c & 0xCC) >> 2 | (c & 0x33) << 2
    c = (c & 0xAA) >> 1 | (c & 0x55) << 1
    return c


def calc_crc16(data):
    crc = CRC_INIT
    for i in range(len(data)):
        c = byte_mirror(data[i]) << 8
        for j in range(8):
            if (crc ^ c) & 0x8000:
                crc = (crc << 1) ^ POLYNOMIAL
            else:
                crc = crc << 1
            crc = crc % 65536
            c = (c << 1) % 65536
    crc = 0xFFFF - crc
    return 256 * byte_mirror(crc // 256) + byte_mirror(crc % 256)


def verify_crc16(input, skip=0, last=2, cut=0):
    lenn = len(input)
    data = input[skip : lenn - last - cut]
    goal = input[lenn - last - cut : lenn - cut]
    if last == 0:
        return hex(calc_crc16(data))
    elif last == 2:
        return calc_crc16(data) == goal[0] * 256 + goal[1]
    return False


##CRC-STUFF DONE

##DECODE-STUFF BEGIN
from Crypto.Cipher import AES


def decode_packet(input):  ##expects input to be bytearray.fromhex(hexstring), full packet  "7ea067..7e"
    if verify_crc16(input, 1, 2, 1):
        nonce = bytes(input[14:22] + input[24:28])  # systemTitle+invocation counter
        cipher = AES.new(binascii.unhexlify(key_smart_meter), AES.MODE_CTR, nonce=nonce, initial_value=2)
        return cipher.decrypt(input[28:-3])
    else:
        return ""


##DECODE-STUFF DONE


def bytes_to_int(bytes):
    result = 0
    for b in bytes:
        result = result * 256 + b
    return result


def show_data(s):
    print("SSS")
    print(s)
    global device
    if device == "WN":
        a = bytes_to_int(s[35:39]) / 1000.000  # +A Wh
        b = bytes_to_int(s[40:44]) / 1000.000  # -A Wh
        c = bytes_to_int(s[45:49]) / 1000.000  # +R varh
        d = bytes_to_int(s[50:54]) / 1000.000  # -R varh
        e = bytes_to_int(s[55:59])  # +P W
        f = bytes_to_int(s[60:64])  # -P W
        g = bytes_to_int(s[65:69])  # +Q var
        h = bytes_to_int(s[70:74])  # -Q var
        yyyy = bytes_to_int(s[22:24])
        mm = bytes_to_int(s[24:25])
        dd = bytes_to_int(s[25:26])
        hh = bytes_to_int(s[27:28])
        mi = bytes_to_int(s[28:29])
        ss = bytes_to_int(s[29:30])
        print(datetime(year=yyyy, month=mm, day=dd, hour=hh, minute=mi, second=ss))
        print(
            "Output: %10.3fkWh, %10.3fkWh, %10.3fkvarh, %10.3fkvarh, %5dW, %5dW, %5dvar, %5dvar at %02d.%02d.%04d-%02d:%02d:%02d"
            % (a, b, c, d, e, f, g, h, dd, mm, yyyy, hh, mi, ss)
        )
    elif device == "KN":
        a = bytes_to_int(s[57:61]) / 1000.000  # +A Wh
        b = bytes_to_int(s[62:66]) / 1000.000  # -A Wh
        c = bytes_to_int(s[67:71]) / 1000.000  # +R varh
        d = bytes_to_int(s[72:76]) / 1000.000  # -R varh
        e = bytes_to_int(s[77:81])  # +P W
        f = bytes_to_int(s[82:86])  # -P W
        yyyy = bytes_to_int(s[51:53])
        mm = bytes_to_int(s[53:54])
        dd = bytes_to_int(s[54:55])
        hh = bytes_to_int(s[45:46])
        mi = bytes_to_int(s[46:47])
        ss = bytes_to_int(s[47:48])
        print(
            "Output: %10.3fkWh, %10.3fkWh, %10.3fkvarh, %10.3fkvarh, %5dW, %5dW at %02d.%02d.%04d-%02d:%02d:%02d"
            % (a, b, c, d, e, f, dd, mm, yyyy, hh, mi, ss)
        )
    else:
        print("Device type not recognized")


dec = decode_packet(bytearray.fromhex(data))
show_data(dec) if (dec) else "CRC error"

binascii.hexlify(dec)

# plaintext hex string of WienerNetze explained
# 0f                          start-byte?
# 0059a374                    packet number, appears to be IC+1 (faked in this example)
# 0c                          intro 12byte-timestamp
# 07e5 01 1b 03 10 0b 2d 00ffc400   timestamp: year,month,day,dow,hours,minutes,seconds
# 020909                      some header for the following 9-value-structure?
# 0c                          intro 12byte-timestamp
# 07e5 01 1b 03 10 0b 2d 00ffc400   timestamp: year,month,day,dow,hours,minutes,seconds
# 06                          intro 32bit-value
# 004484bc                    +A Wh
# 06                          intro 32bit-value
# 0000053e                    -A Wh
# 06                          intro 32bit-value
# 0001004b                    +R varh
# 06                          intro 32bit-value
# 001c20f1                    -R varh
# 06                          intro 32bit-value
# 00000176                    +P W
# 06                          intro 32bit-value
# 00000000                    -P W
# 06                          intro 32bit-value
# 00000000                    +Q var
# 06                          intro 32bit-value
# 000000f4                    -Q var

# plaintext hex string of KärntenNetz explained
# 0f
# 0002e9fa
# 0c
# 07e5 08 01 07 0c 05 32 00ff8880 # 01.08.2021 12:05:50
# 02 0c
# 0906 0006190900ff               # 0.6.25.9.0.255 Firmwareversion?
# 090d 31313231323731363030303030 # 1121271600000  S/N?
# 0904 0c053200                   # 12:05:50.000   Time
# 0905 07e5080100                 # 01.Aug.2021    Date
# 06 01fa3e2a                     # 33177130 +A Wh
# 06 00000000                     #     0000 -A Wh
# 06 0088de3d                     #  8969789 +R varh
# 06 00fd4489                     # 16598153 -R varh
# 06 00000c4d                     #     3149 +P W
# 06 00000000                     #     0000 -P W
# 0900                            # Customer info text
# 0900                            # Customer info code
