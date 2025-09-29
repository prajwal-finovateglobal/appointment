from fastapi import APIRouter, HTTPException
from typing import Dict

from models import BatchAvailabilityRequest, AvailabilityResponse, DateRangeAvailabilityRequest, FreeSlotsResponse
from services import AvailabilityService

router = APIRouter(prefix="/availability")


@router.post("/batch", response_model=AvailabilityResponse)
def availability_batch(request: BatchAvailabilityRequest) -> AvailabilityResponse:
    """Check availability for multiple date/time slots in batch using Google Calendar"""
    try:
        availability_service = AvailabilityService()
        
        # Convert slots to the format expected by the service
        slots_data = [{"date": slot.date, "times": slot.times} for slot in request.slots]
        
        # Get availability for all slots using Google Calendar
        results = availability_service.get_availability_for_slots(
            slots_data, 
            request.timezone,
            duration_minutes=request.duration_minutes
        )
        
        return AvailabilityResponse(
            timezone=request.timezone,
            duration_minutes=request.duration_minutes,
            results=results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/free-slots", response_model=FreeSlotsResponse)
def get_free_slots(request: DateRangeAvailabilityRequest) -> FreeSlotsResponse:
    """Get all free slots within a date range using Google Calendar"""
    try:
        availability_service = AvailabilityService()
        
        # Get free slots for the date range
        free_slots = availability_service.get_free_slots_for_date_range(
            start_date=request.start_date,
            end_date=request.end_date,
            timezone=request.timezone,
            duration_minutes=request.duration_minutes,
            working_hours=request.working_hours
        )
        
        return FreeSlotsResponse(
            timezone=request.timezone,
            duration_minutes=request.duration_minutes,
            working_hours=request.working_hours,
            free_slots=free_slots
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "google-calendar-availability"}
