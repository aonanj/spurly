"""
Defines base and derived dataclasses for handling user and connection profiles.

BaseProfile:
    name: Optional[str] - Optional name of the profile owner.
    age: [int] - age of the profile owner; must be >= 18.
    gender: Optional[str] - Optional gender of the profile owner.
    pronouns: Optional[str] - Optional preferred pronouns.
    school: Optional[str] - Optional school associated with the profile.
    job: Optional[str] - Optional occupation or job title.
    drinking: Optional[str] - Optional drinking habits or preferences.
    ethnicity: Optional[str] - Optional ethnicity of the profile owner.
    hometown: Optional[str] - Optional hometown or place of origin.
    greenlights: Optional[List[str]] - Optional list of likes, interests, or signals.
    redlights: Optional[List[str]] - Optional list of dislikes or signals.
    personality_traits: Optional[List[str]] - Optional list of personality traits.
    
    to_dict returns a BaseProfile object formatted as a python dictionary.

UserProfile (inherits from BaseProfile):
    user_id: str - Unique identifier for the user.
    selected_spurs: List[str] - List of the spurs to be generated for a user. Default is all.

    from_dict converts a python dictionary into a custom UserProfile object.

ConnectionProfile (inherits from BaseProfile):
    connection_id: str - Unique identifier for the connection.
    user_id: str - Identifier for the associated user (each connection is linked to one user).
    

    from_dict converts a python dictionary into a custom ConnectionProfile object.
"""

from dataclasses import dataclass
from typing import Optional, List

@dataclass
class BaseProfile:
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

@dataclass
class UserProfile(BaseProfile):
    user_id: str
    selected_spurs: List[str]

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class ConnectionProfile(BaseProfile):
    connection_id: str
    # The associated user's ID; every connection must be linked to a user.
    user_id: str

    @classmethod
    def from_dict(cls, data):
        return cls(**data)