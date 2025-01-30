import pytest
import os
from app.energy_agent.smartfox import extract_wr_energy_values, get_produced_energy


def load_xml_file(file: str):
    if not os.path.exists(file):
        return ""

    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
        return content
    return ""


smart_fox_data = [
    {
        "xml_file_content": load_xml_file("./tests/smart_fox/st2.xml"),
        "num_values": 5,  # Add your expected value count
        "production": 15827.5,  # Add your expected production value
    },
    {
        "xml_file_content": load_xml_file("./tests/smart_fox/st5.xml"),
        "num_values": 5,  # Add your expected value count
        "production": 22090.4,  # Add your expected production value
    },
    {
        "xml_file_content": load_xml_file("./tests/smart_fox/st6.xml"),
        "num_values": 5,  # Add your expected value count
        "production": 18377.6,  # Add your expected production value
    },
    {
        "xml_file_content": load_xml_file("./tests/smart_fox/st7.xml"),
        "num_values": 5,  # Add your expected value count
        "production": 80047.77,  # Add your expected production value
    },
]


def test_extract_wr_values():
    for test in smart_fox_data:
        content = test["xml_file_content"]
        assert len(content) > 0

        values = extract_wr_energy_values(content)
        assert values
        assert test["num_values"] == len(values)

        production = 0
        for key in values:
            production = production + values[key]
        assert test["production"] == production


def test_compute_production():
    for test in smart_fox_data:
        content = test["xml_file_content"]
        assert len(content) > 0

        production = get_produced_energy(content)
        assert test["production"] == production
