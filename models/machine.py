from dataclasses import dataclass, asdict


@dataclass
class Machine:
    cid: int
    machine: dict

    def to_dict(self):
        return asdict(self)
