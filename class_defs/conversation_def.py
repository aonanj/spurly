from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class Conversation:
    user_id: str
    conversation_id: str
    conversation: List[Dict[str, Any]]
    connection_id: Optional[str]
    situation: Optional[str]
    topic: Optional[str]
    spurs: Optional[Dict[str, Any]]
    created_at: datetime

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

