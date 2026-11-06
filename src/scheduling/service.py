from datetime import date

from src.scheduling.models import (
    BookingRequest,
    AvailabilitySlot,
    BookingConfirmation,
)
from src.scheduling.provider import MockCalendlyProvider

class SchedulingService:
    """Application service for appointment scheduling."""

    def __init__(self, provider=None):
        self.provider = provider or MockCalendlyProvider()

    async def get_availability(
        self,
        start_date: date,
        days: int = 7,
    ) -> list[AvailabilitySlot]:
        """Return available appointment slots."""

        return await self.provider.get_availability(
            start_date=start_date,
            days=days,
        )

    async def create_booking(
        self,
        request: BookingRequest,
    ) -> BookingConfirmation:
        """Create an appointment booking."""

        return await self.provider.create_booking(request)