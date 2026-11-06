from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

class ConversationMessage(BaseModel):
    """A single message exchanged during a conversation."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class CallerProfile(BaseModel):
    """Structured information collected about a caller."""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    email_confirmed: bool = False
    phone: str | None = None

    looking_for: Literal["self", "someone_else"] | None = None
    preferred_location: str | None = None

class ConversationState(BaseModel):
    """Complete state of an active caller conversation."""

    model_config = ConfigDict(validate_assignment=True)

    session_id: str
    status: Literal["active", "completed", "transferred"] = "active"

    caller: CallerProfile = Field(default_factory=CallerProfile)

    discovery_answers: dict[str, str] = Field(default_factory=dict)
    messages: list[ConversationMessage] = Field(default_factory=list)

    conversation_summary: str | None = None
    current_stage: str = "greeting"

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
