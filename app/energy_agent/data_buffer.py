from collections import OrderedDict
import threading
import json
from typing import Dict
from app.helpers.logs import log


class DataBuffer:
    def __init__(self):
        self._buffer: OrderedDict = OrderedDict()
        self._lock = threading.Lock()

    @log
    def add_data(self, data: Dict) -> None:
        with self._lock:
            for key, value in data.items():
                self._buffer[key] = value

    @log
    def get_data(self) -> Dict:
        with self._lock:
            return self._buffer

    @log
    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()

    @log
    def is_empty(self) -> bool:
        with self._lock:
            return self._buffer == {}

    @log
    def to_json(self) -> str:
        with self._lock:
            return json.dumps([{k: v} for k, v in self._buffer.items()])
