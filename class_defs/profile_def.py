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

from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class BaseProfile:
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    pronouns: Optional[str] = None
    school: Optional[str] = None
    job: Optional[str] = None
    drinking: Optional[str] = None
    ethnicity: Optional[str] = None
    current_city: Optional[str] = None
    hometown: Optional[str] = None
    looking_for: Optional[str] = None
    greenlights: Optional[List[str]] = field(default_factory=list)
    redlights: Optional[List[str]] = field(default_factory=list)

    
    personality_traits: Optional[List[str]] = field(default_factory=list)

    def to_dict(self):
        return self.__dict__

@dataclass
class UserProfile(BaseProfile):
    user_id: str = ""
    selected_spurs: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    @classmethod
    def get_attr_as_str(cls, profile_instance: "UserProfile", attr_key: str) -> str:
        """
        Retrieve the value of an attribute from a given UserProfile instance
        and return it as a string.

        Args:
            profile_instance (UserProfile): The profile object to inspect.
            attr_key (str): The attribute name to retrieve.

        Returns:
            str: The attribute value converted to a string, or an empty string if
                 the attribute does not exist or is None.
        """
        value = getattr(profile_instance, attr_key, None)
        return "" if value is None else str(value)

@dataclass
class ConnectionProfile(BaseProfile):
    connection_id: str = ""
    # The associated user's ID; every connection must be linked to a user.
    user_id: str = ""

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    @classmethod
    def get_attr_as_str(cls, profile_instance: "ConnectionProfile", attr_key: str) -> str:
        """
        Retrieve the value of an attribute from a given ConnectionProfile instance
        and return it as a string.

        Args:
            profile_instance (ConnectionProfile): The profile object to inspect.
            attr_key (str): The attribute name to retrieve.

        Returns:
            str: The attribute value converted to a string, or an empty string if
                 the attribute does not exist or is None.
        """
        value = getattr(profile_instance, attr_key, None)
        return "" if value is None else str(value)