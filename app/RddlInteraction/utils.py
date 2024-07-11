import binascii
from typing import List, Dict, Any

from fastapi import HTTPException


def toHexString(data: str) -> str:
    hexBytes = binascii.hexlify(data.encode("utf-8"))
    hexString = hexBytes.decode("utf-8")
    return hexString


def fromHexString(hexString: str) -> str:
    dataString = binascii.unhexlify(hexString.encode("utf-8")).decode("utf-8")
    return dataString


def table_pagination(page: int, page_size: int, data: List[Any]) -> List[Dict]:
    if page is not None and page_size is not None:
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        if start_idx >= len(data):
            raise HTTPException(status_code=400, detail="Invalid page number.")

        data = data[start_idx:end_idx]
    return data
