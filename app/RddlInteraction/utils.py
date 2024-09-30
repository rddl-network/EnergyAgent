import binascii
from typing import List, Dict, Any
from app.helpers.logs import logger
import time
from functools import wraps

from fastapi import HTTPException


def toHexString(data: str) -> str:
    logger.debug(f"toHexString: {data}")
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


class NoValidDataFoundError(Exception):
    """
    Exception raised for errors in the input data when no valid data is found.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="No valid data found"):
        self.message = message
        super().__init__(self.message)


def retry_on_no_valid_data(retries=3, delay=1):
    """
    Decorator that retries a function if NoValidDataFoundError is raised.

    :param retries: Number of retry attempts.
    :param delay: Delay between retries in seconds.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except NoValidDataFoundError as e:
                    logger.info(f"{e}, retrying... ({attempt + 1}/{retries})")
                    attempt += 1
                    time.sleep(delay)
            raise NoValidDataFoundError(f"Failed after {retries} attempts")

        return wrapper

    return decorator
