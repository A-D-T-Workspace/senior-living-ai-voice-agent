from datetime import date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from src.scheduling.models import (
    AvailabilitySlot,
    BookingConfirmation,
    BookingRequest,
)

class MockCalendlyProvider:
    """Simulate Calendly availability and appointment bookings."""

    TIMEZONE = ZoneInfo("Africa/Lagos")
    APPOINTMENT_DURATION_MINUTES = 60

    async def get_availability(
        self,
        start_date: date,
        days: int = 7,
    ) -> list[AvailabilitySlot]:
        """Generate mock weekday appointment slots."""

        slots = []

        for offset in range(days):
            current_date = start_date + timedelta(days=offset)

            if current_date.weekday() >= 5:
                continue

            for hour in (10, 14):
                start_time = datetime.combine(
                    current_date,
                    time(hour=hour),
                    tzinfo=self.TIMEZONE,
                )

                end_time = start_time + timedelta(
                    minutes=self.APPOINTMENT_DURATION_MINUTES
                )

                slots.append(
                    AvailabilitySlot(
                        start_time=start_time,
                        end_time=end_time,
                    )
                )

        return slots

    async def create_booking(
        self,
        request: BookingRequest,
    ) -> BookingConfirmation:
        """Simulate a booking for an available appointment slot."""

        requested_time = request.preferred_start

        if requested_time.tzinfo is None:
            requested_time = requested_time.replace(
                tzinfo=ZoneInfo(request.timezone)
            )

        requested_time = requested_time.astimezone(self.TIMEZONE)

        available_slots = await self.get_availability(
            start_date=requested_time.date(),
            days=1,
        )

        matching_slot = next(
            (
                slot
                for slot in available_slots
                if slot.start_time == requested_time
            ),
            None,
        )

        if matching_slot is None:
            raise ValueError("The requested appointment slot is unavailable.")

        return BookingConfirmation(
            booking_id=str(uuid4()),
            status="confirmed",
            appointment_type=request.appointment_type,
            start_time=matching_slot.start_time,
            end_time=matching_slot.end_time,
            invitee_email=request.email,
            meeting_url=None,
        )
