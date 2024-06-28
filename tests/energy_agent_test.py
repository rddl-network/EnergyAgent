from app.helpers.config_helper import extract_client_id


def test_extract_client_id():
    topic = "rddl/SMD/shelly_12345_asgasd/status/switch:0,"
    assert extract_client_id(topic) == "shelly_12345_asgasd"


def test_extract_client_id_2():
    topic = "rddl/SMD/shelly_12345_asgasd/switch:0,"
    assert extract_client_id(topic) == "shelly_12345_asgasd"


def test_extract_client_id_negative():
    topic = "rddl/SMD/"
    assert extract_client_id(topic) == ""


# client_id = 'shellyplusplugs-e465b8b8e404'
# data = {"id": 0, "source": "init", "output": True, "apower": 0.0, "voltage": 231.6, "current": 0.000,
#        "aenergy": {"total": 29.216, "by_minute": [0.000, 0.000, 0.000], "minute_ts": 1718855819},
#        "temperature": {"tC": 50.7, "tF": 123.2}}
