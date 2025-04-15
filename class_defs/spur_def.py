"""
Defines a dataclass named Spur with the following fields:
    user_id: User ID (string)
    spur_id: Spur ID (string)
    conversation_id: Conversation ID (string). Concatenates user_id, ":", and a UUID4.
    conversation: List of message dictionaries representing the conversation between the user and a connection.
    connection_id: Optional identifier for the connection (string) involved in the conversation.
    situation: Optional description of the contextual situation of the conversation (string).
    topic: Optional subject or theme of the conversation (string).
    variant: spur variant type of this spur.
    text: text of the spur.
    created_at: Datetime indicating when spur was generated.
    
    to_dict returns a Spur object formatted as a python dictionary.
    from_dict converts a python dictionary into a custom Spur object.

"""

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