from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class BookingRequest(BaseModel):
    """Validated request to book a senior living appointment."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=5, max_length=30)
    appointment_type: Literal["community_tour", "introductory_consultation"]
    preferred_start: datetime
    timezone: str = "Africa/Lagos"

class AvailabilitySlot(BaseModel):
    """An available appointment time."""

    model_config = ConfigDict(extra="forbid")

    start_time: datetime
    end_time: datetime


class BookingConfirmation(BaseModel):
    """Result returned after a successful booking."""

    model_config = ConfigDict(extra="forbid")

    booking_id: str
    status: Literal["confirmed", "pending"]
    appointment_type: Literal["community_tour", "introductory_consultation"]
    start_time: datetime
    end_time: datetime
    invitee_email: EmailStr
    meeting_url: str | None = None
