from dataclasses import dataclass, field
from typing import List

@dataclass
class Individuo:
    genes: List[int] = field(default_factory=list)
    fitness: float = 0.0
