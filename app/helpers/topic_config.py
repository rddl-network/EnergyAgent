import json
from dataclasses import dataclass


@dataclass(slots=True)
class TopicConfig:
    def __init__(self):
        self.topics: list[str] = []
