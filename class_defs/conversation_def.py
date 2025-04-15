"""
Defines a dataclass named Conversation with the following fields:
    user_id: User ID (string)
    conversation_id: Conversation ID (string). Concatenates user_id, ":", and a UUID4.
    conversation: List of message dictionaries representing the conversation between the user and a connection.
    connection_id: Optional identifier for the connection (string) involved in the conversation.
    situation: Optional description of the contextual situation of the conversation (string).
    topic: Optional subject or theme of the conversation (string).
    spurs: Optional additional metadata or prompts (dictionary) related to the conversation.
    created_at: Datetime indicating when the conversation was initiated.
    
    to_dict returns a Conversation object formatted as a python dictionary.
    from_dict converts a python dictionary into a custom Conversation object.
"""

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
