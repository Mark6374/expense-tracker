from dataclasses import dataclass, asdict


@dataclass
class Expense:
    date: str
    category: str
    description: str
    amount: float

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Expense(d["date"], d["category"], d["description"], float(d["amount"]))
