from dataclasses import dataclass
from enum import Enum


class DetectionClass(Enum):
    PERSON = 0
    CAT = 15
    DOG = 16
    BACKPACK = 24


@dataclass(frozen=True)
class Detection:
    cls: DetectionClass
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def is_person(self) -> bool:
        return self.cls == DetectionClass.PERSON
