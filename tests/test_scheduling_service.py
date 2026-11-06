from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from src.scheduling.models import BookingRequest
from src.scheduling.service import SchedulingService

@pytest.mark.asyncio
async def test_service_returns_availability():
    service = SchedulingService()

    slots = await service.get_availability(
        start_date=date(2026, 11, 9),
        days=7,
    )

    assert len(slots) == 10
    assert all(slot.start_time.weekday() < 5 for slot in slots)

@pytest.mark.asyncio
async def test_service_creates_booking():
    service = SchedulingService()

    request = BookingRequest(
        first_name="Ada",
        last_name="Okafor",
        email="ada@example.com",
        phone="+2348012345678",
        appointment_type="community_tour",
        preferred_start=datetime(
            2026, 11, 9, 10, 0,
            tzinfo=ZoneInfo("Africa/Lagos"),
        ),
    )

    confirmation = await service.create_booking(request)

    assert confirmation.status == "confirmed"
    assert confirmation.invitee_email == "ada@example.com"
    assert confirmation.appointment_type == "community_tour"