from dataclasses import dataclass
from typing import Optional, List

@dataclass
class Profile:
    user_id: str
    name: Optional[str]
    age: Optional[int]
    gender: Optional[str]
    pronouns: Optional[str]
    school: Optional[str]
    job: Optional[str]
    drinking: Optional[str]
    ethnicity: Optional[str]
    hometown: Optional[str]
    greenlights: Optional[List[str]]
    redlights: Optional[List[str]]
    personality_traits: Optional[List[str]] = None

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)