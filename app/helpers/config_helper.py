import json


def save_config(path_to_topic_config: str, config: dict):
    with open(path_to_topic_config, "w") as f:
        json.dump(config, f)


def load_config(path_to_topic_config: str) -> dict:
    try:
        with open(path_to_topic_config, "r") as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration file: {e}")
        return {}
