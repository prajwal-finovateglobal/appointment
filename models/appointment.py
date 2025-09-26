from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class AppointmentStatus(str, Enum):
    OFFERED = "offered"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class AppointmentDetail(BaseModel):
    date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    time: str = Field(..., description="Appointment time in HH:MM format")
    day_name: Optional[str] = Field(None, description="Day of the week")
    status: AppointmentStatus = Field(default=AppointmentStatus.OFFERED)
    duration: Optional[str] = Field(None, description="Expected duration")
    appointment_type: Optional[str] = Field(None, description="Type of appointment")

class ExtractedAppointments(BaseModel):
    appointments: List[AppointmentDetail] = Field(default_factory=list)
    customer_name: Optional[str] = Field(None, description="Customer name")
    contact_info: Optional[str] = Field(None, description="Customer contact")
    context: Optional[str] = Field(None, description="Additional context")
    confidence_score: float = Field(default=0.0, description="Extraction confidence")

class AppointmentExtractionResponse(BaseModel):
    success: bool = Field(default=True)
    data: ExtractedAppointments = Field(...)
    message: str = Field(default="Appointments extracted successfully")
    processing_time: float = Field(default=0.0)