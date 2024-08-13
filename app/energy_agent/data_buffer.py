from collections import OrderedDict
import threading
import json
from typing import Dict, Any
from app.helpers.logs import log

class DataBuffer:
    def __init__(self):
        self._buffer: OrderedDict[str, str] = OrderedDict()
        self._lock = threading.Lock()

    @log
    def add_data(self, data: Dict[str, str]) -> None:
        with self._lock:
            for key, value in data.items():
                parsed_value = json.loads(value)
                if key in self._buffer:
                    self._buffer.move_to_end(key)  # Move existing key to the end to maintain recency
                self._buffer[key] = parsed_value

    @log
    def get_data(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._buffer)

    @log
    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()

    @log
    def is_empty(self) -> bool:
        with self._lock:
            return len(self._buffer) == 0

    @log
    def size(self) -> int:
        with self._lock:
            return len(self._buffer)

    @log
    def to_json(self) -> str:
        with self._lock:
            return json.dumps([{k: json.dumps(v)} for k, v in self._buffer.items()])