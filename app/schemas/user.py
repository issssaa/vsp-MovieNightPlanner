"""Pydantic schemas for User request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Usernames are used in URLs and shown on a shared group screen, so keep them to
# an unambiguous character set rather than accepting arbitrary text.
USERNAME_PATTERN = r"^[A-Za-z0-9_-]+$"


class UserCreate(BaseModel):
    """Payload for creating a user. No password — see Design Decision 5."""

    username: str = Field(min_length=1, max_length=50, pattern=USERNAME_PATTERN)
    display_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("username")
    @classmethod
    def lowercase_username(cls, value: str) -> str:
        """Store usernames lowercased so `Alice` and `alice` cannot both exist."""
        return value.lower()

    @field_validator("display_name")
    @classmethod
    def blank_display_name_is_none(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class UserRead(BaseModel):
    """Response model returned to clients."""

    id: int
    username: str
    display_name: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
