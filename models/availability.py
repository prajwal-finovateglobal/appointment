from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple, Any
from utils.config import settings


class Slot(BaseModel):
    date: str = Field(..., description="ISO date, e.g., 2025-09-29")
    times: List[str] = Field(..., description="List of HH:MM times in local timezone, e.g., ['09:00','10:30']")


class BatchAvailabilityRequest(BaseModel):
    timezone: str = Field(default_factory=lambda: settings.default_timezone, description="Timezone for the slots")
    duration_minutes: int = Field(default=60, description="Duration of each slot in minutes")
    slots: List[Slot]


class DateRangeAvailabilityRequest(BaseModel):
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    timezone: str = Field(default_factory=lambda: settings.default_timezone, description="Timezone for the slots")
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


class EventListRequest(BaseModel):
    """Request model for listing events in a date range"""
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    timezone: str = Field(default_factory=lambda: settings.default_timezone, description="Timezone for the events")
    calendar_id: str = Field(default="primary", description="Google Calendar ID")


class EventDetail(BaseModel):
    """Model for individual event details"""
    event_id: str = Field(..., description="Google Calendar event ID")
    title: str = Field(..., description="Event title")
    start: str = Field(..., description="Event start time")
    end: str = Field(..., description="Event end time")
    location: Optional[str] = Field(default=None, description="Event location")
    description: Optional[str] = Field(default=None, description="Event description")
    attendees: List[Dict[str, Any]] = Field(default_factory=list, description="Event attendees")
    meeting_link: Optional[str] = Field(default=None, description="Meeting link if available")
    status: str = Field(default="confirmed", description="Event status")


class EventListResponse(BaseModel):
    """Response model for event list"""
    timezone: str
    start_date: str
    end_date: str
    total_events: int
    events: List[EventDetail]
    calendar_info: Dict[str, str] = Field(default_factory=lambda: {
        "provider": "Google Calendar",
        "calendar_id": "primary"
    })
