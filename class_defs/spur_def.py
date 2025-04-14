from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class Spur:
    user_id: str
    spur_id: str
    conversation_id: Optional[str]
    connection_id: Optional[str]
    situation: Optional[str]
    topic: Optional[str]
    variant: Optional[str]
    tone: Optional[str]
    text: Optional[str]
    created_at: datetime

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)