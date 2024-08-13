import pytest
import json
from threading import Thread

from app.energy_agent.data_buffer import DataBuffer


@pytest.fixture
def buffer():
    return DataBuffer()


def test_add_data(buffer):
    buffer.add_data({"key1": "value1", "key2": "value2"})
    assert buffer.get_data() == {"key1": "value1", "key2": "value2"}


def test_get_data(buffer):
    buffer.add_data({"key1": "value1"})
    assert buffer.get_data() == {"key1": "value1"}


def test_clear(buffer):
    buffer.add_data({"key1": "value1"})
    buffer.clear()
    assert buffer.is_empty()


def test_is_empty(buffer):
    assert buffer.is_empty()
    buffer.add_data({"key1": "value1"})
    assert not buffer.is_empty()


def test_to_json(buffer):
    buffer.add_data({"key1": "value1", "key2": "value2"})
    expected_json = json.dumps([{"key1": "value1"}, {"key2": "value2"}])
    assert buffer.to_json() == expected_json


def test_thread_safety(buffer):
    def add_data():
        for i in range(1000):
            buffer.add_data({f"key{i}": f"value{i}"})

    threads = [Thread(target=add_data) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(buffer.get_data()) == 1000


def test_order_preservation(buffer):
    data = {"a": 1, "b": 2, "c": 3}
    buffer.add_data(data)
    assert list(buffer.get_data().items()) == list(data.items())
