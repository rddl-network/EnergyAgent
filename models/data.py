from dataclasses import dataclass, asdict


@dataclass
class Data:
    cid: int
    timestamp: int
    kwh: float

    def to_dict(self):
        return asdict(self)
