import json
import os


def save_config(path_to_config: str, config_to_save: dict):
    with open(path_to_config, "w") as f:
        json.dump(config_to_save, f)


def remove_config(path_to_config: str):
    if os.path.exists(path_to_config):
        os.remove(path_to_config)


def load_config(path_to_config: str) -> dict:
    try:
        if os.path.exists(path_to_config):
            with open(path_to_config, "r") as f:
                data = json.load(f)
            return data
        else:
            return {}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration file: {e}")
        return {}


def build_config_path(base_path: str, filename: str) -> str:
    return f"{base_path}/{filename}"


def extract_client_id(topic):
    """
    Extracts the client ID from the topic.
    Assumes topic format: rddl/SMD/<client_id>/*
    """
    parts = topic.split("/")
    if len(parts) >= 3:
        return parts[2]
    else:
        return None
