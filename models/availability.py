from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple


class Slot(BaseModel):
    date: str = Field(..., description="ISO date, e.g., 2025-09-29")
    times: List[str] = Field(..., description="List of HH:MM times in local timezone, e.g., ['09:00','10:30']")


class BatchAvailabilityRequest(BaseModel):
    timezone: str = Field(default="UTC", description="Timezone for the slots")
    duration_minutes: int = Field(default=60, description="Duration of each slot in minutes")
    slots: List[Slot]


class DateRangeAvailabilityRequest(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    timezone: str = Field(default="UTC", description="Timezone for the slots")
    duration_minutes: int = Field(default=60, description="Duration of each slot in minutes")
    working_hours: Tuple[int, int] = Field(default=(9, 17), description="Working hours as (start_hour, end_hour) in 24-hour format")


class AvailabilityResponse(BaseModel):
    timezone: str
    duration_minutes: int
    results: Dict[str, Dict[str, Dict]]
    calendar_info: Dict[str, str] = Field(default_factory=lambda: {
        "provider": "Google Calendar",
        "calendar_id": "primary"
    })


class FreeSlotsResponse(BaseModel):
    timezone: str
    duration_minutes: int
    working_hours: Tuple[int, int]
    free_slots: Dict[str, List[str]]  # date -> list of available times
    calendar_info: Dict[str, str] = Field(default_factory=lambda: {
        "provider": "Google Calendar", 
        "calendar_id": "primary"
    })
