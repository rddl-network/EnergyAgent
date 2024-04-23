import json


def save_config(path_to_config: str, config_to_save: dict):
    with open(path_to_config, "w") as f:
        json.dump(config_to_save, f)


def load_config(path_to_config: str) -> dict:
    try:
        with open(path_to_config, "r") as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration file: {e}")
        return {}


def build_config_path(base_path: str, filename: str) -> str:
    return f"{base_path}/{filename}"
