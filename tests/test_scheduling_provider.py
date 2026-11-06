from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from src.scheduling.provider import MockCalendlyProvider
from src.scheduling.models import BookingRequest

@pytest.mark.asyncio
async def test_get_availability_returns_weekday_slots():
    provider = MockCalendlyProvider()

    slots = await provider.get_availability(
        start_date=date(2026, 11, 9),
        days=7,
    )

    assert len(slots) == 10

    for slot in slots:
        assert slot.start_time.weekday() < 5
        assert slot.start_time.tzinfo == ZoneInfo("Africa/Lagos")
        assert (slot.end_time - slot.start_time).total_seconds() == 3600

@pytest.mark.asyncio
async def test_create_booking_confirms_available_slot():
    provider = MockCalendlyProvider()

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

    confirmation = await provider.create_booking(request)

    assert confirmation.status == "confirmed"
    assert confirmation.appointment_type == "community_tour"
    assert confirmation.invitee_email == "ada@example.com"
    assert confirmation.start_time.hour == 10

@pytest.mark.asyncio
async def test_create_booking_rejects_unavailable_slot():
    provider = MockCalendlyProvider()

    request = BookingRequest(
        first_name="Ada",
        last_name="Okafor",
        email="ada@example.com",
        phone="+2348012345678",
        appointment_type="community_tour",
        preferred_start=datetime(
            2026, 11, 9, 12, 0,
            tzinfo=ZoneInfo("Africa/Lagos"),
        ),
    )

    with pytest.raises(ValueError, match="requested appointment slot is unavailable"):
        await provider.create_booking(request)