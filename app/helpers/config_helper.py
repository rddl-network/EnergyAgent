import json


def save_topic_config(self, path_to_topic_config: str):
    with open(path_to_topic_config, "w") as f:
        json.dump(self.__dict__, f)


def load_topic_config(path_to_topic_config: str):
    try:
        with open(path_to_topic_config, "r") as f:
            data = json.load(f)
        return dict(data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration file: {e}")
        return None


def save_topics(path_to_topic_config: str, topics: list[str]):
    with open(path_to_topic_config, "w") as f:
        json.dump(topics, f)


def load_config_file(path_to_topic_config: str) -> list[str]:
    try:
        with open(path_to_topic_config, "r") as f:
            data = json.load(f)
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading configuration file: {e}")
        return []
