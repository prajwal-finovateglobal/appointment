from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MeetingLocation(BaseModel):
    """Meeting location details"""
    type: str = Field(default="virtual", description="Location type: 'virtual', 'physical', 'phone'")
    address: Optional[str] = Field(default=None, description="Physical address if type is 'physical'")
    meeting_link: Optional[str] = Field(default=None, description="External meeting link (Zoom, Teams, etc.) - NOT for Google Meet")
    phone_number: Optional[str] = Field(default=None, description="Phone number if type is 'phone'")


class AttendeeInfo(BaseModel):
    """Model for attendee information"""
    name: str = Field(..., description="Attendee's name")
    email: EmailStr = Field(..., description="Attendee's email address")


class GoogleCalendarBookingRequest(BaseModel):
    """Request model for creating a Google Calendar booking"""
    # Event details
    title: str = Field(..., description="Event title/name")
    description: Optional[str] = Field(default=None, description="Event description")
    date: str = Field(..., description="Event date in YYYY-MM-DD format")
    time: str = Field(..., description="Event time in HH:MM format (24-hour)")
    duration_minutes: int = Field(default=60, description="Event duration in minutes")
    timezone: str = Field(default="Asia/Kolkata", description="Event timezone")
    
    # Attendee details
    organizer_name: str = Field(..., description="Name of the person organizing the meeting")
    organizer_email: EmailStr = Field(..., description="Email of the person organizing the meeting")
    attendee_name: str = Field(..., description="Name of the primary attendee")
    attendee_email: EmailStr = Field(..., description="Email of the primary attendee")
    additional_attendees: Optional[List[EmailStr]] = Field(default=None, description="Additional attendee emails")
    # Alternative: Use structured attendee list
    all_attendees: Optional[List[AttendeeInfo]] = Field(default=None, description="Complete list of attendees with names and emails")
    
    # Meeting details
    location: Optional[MeetingLocation] = Field(default=None, description="Meeting location details")
    meeting_notes: Optional[str] = Field(default=None, description="Additional meeting notes")
    send_notifications: bool = Field(default=True, description="Whether to send email notifications")
    
    # Calendar settings
    calendar_id: str = Field(default="primary", description="Google Calendar ID to create event in")
    visibility: str = Field(default="default", description="Event visibility: 'default', 'public', 'private'")


class GoogleCalendarBookingResponse(BaseModel):
    """Response model for Google Calendar booking creation"""
    success: bool = Field(..., description="Whether the booking was successful")
    event_id: str = Field(..., description="Google Calendar event ID")
    event_link: str = Field(..., description="Google Calendar event link")
    meeting_link: Optional[str] = Field(default=None, description="Video meeting link if applicable")
    event_details: Dict[str, Any] = Field(..., description="Created event details")
    message: str = Field(..., description="Success or error message")
    calendar_info: Dict[str, str] = Field(default_factory=lambda: {
        "provider": "Google Calendar",
        "calendar_id": "primary"
    })


class BookingStatus(str, Enum):
    """Booking status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class BookingUpdateRequest(BaseModel):
    """Request model for updating a Google Calendar booking"""
    event_id: str = Field(..., description="Google Calendar event ID to update")
    title: Optional[str] = Field(default=None, description="New event title")
    description: Optional[str] = Field(default=None, description="New event description")
    date: Optional[str] = Field(default=None, description="New event date in YYYY-MM-DD format")
    time: Optional[str] = Field(default=None, description="New event time in HH:MM format")
    duration_minutes: Optional[int] = Field(default=None, description="New event duration in minutes")
    location: Optional[MeetingLocation] = Field(default=None, description="New meeting location")
    meeting_notes: Optional[str] = Field(default=None, description="New meeting notes")
    send_notifications: bool = Field(default=True, description="Whether to send update notifications")


class BookingCancellationRequest(BaseModel):
    """Request model for cancelling a Google Calendar booking"""
    event_id: str = Field(..., description="Google Calendar event ID to cancel")
    reason: Optional[str] = Field(default=None, description="Cancellation reason")
    send_notifications: bool = Field(default=True, description="Whether to send cancellation notifications")
