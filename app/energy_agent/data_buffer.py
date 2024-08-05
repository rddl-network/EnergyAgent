import threading
import json
from typing import List, Any
from app.helpers.logs import log


class DataBuffer:
    def __init__(self):
        self._buffer: List[Any] = []
        self._lock = threading.Lock()

    @log
    def add_data(self, data: Any) -> None:
        with self._lock:
            self._buffer.append(data)

    @log
    def get_data(self) -> List[Any]:
        with self._lock:
            return self._buffer.copy()

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
            return json.dumps(self._buffer)
