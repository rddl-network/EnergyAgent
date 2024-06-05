import binascii


def toHexString(data: str) -> str:
    hexBytes = binascii.hexlify(data.encode("utf-8"))
    hexString = hexBytes.decode("utf-8")
    return hexString


def fromHexString(hexString: str) -> str:
    dataString = binascii.unhexlify(hexString.encode("utf-8")).decode("utf-8")
    return dataString
