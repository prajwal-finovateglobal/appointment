from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from models.booking import (
    GoogleCalendarBookingRequest, 
    GoogleCalendarBookingResponse,
    BookingUpdateRequest,
    BookingCancellationRequest
)
from services.google_calendar_booking_service import GoogleCalendarBookingService

router = APIRouter(prefix="/booking")


@router.post("/create", response_model=GoogleCalendarBookingResponse)
def create_booking(request: GoogleCalendarBookingRequest) -> GoogleCalendarBookingResponse:
    """Create a new Google Calendar booking/event"""
    try:
        booking_service = GoogleCalendarBookingService()
        
        # Create the booking
        response = booking_service.create_booking(request)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/update", response_model=GoogleCalendarBookingResponse)
def update_booking(request: BookingUpdateRequest) -> GoogleCalendarBookingResponse:
    """Update an existing Google Calendar booking/event"""
    try:
        booking_service = GoogleCalendarBookingService()
        
        # Update the booking
        response = booking_service.update_booking(request)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/cancel")
def cancel_booking(request: BookingCancellationRequest) -> Dict[str, Any]:
    """Cancel a Google Calendar booking/event"""
    try:
        booking_service = GoogleCalendarBookingService()
        
        # Cancel the booking
        response = booking_service.cancel_booking(request)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/details/{event_id}")
def get_booking_details(event_id: str) -> Dict[str, Any]:
    """Get details of a specific Google Calendar booking/event"""
    try:
        booking_service = GoogleCalendarBookingService()
        
        # Get booking details
        response = booking_service.get_booking_details(event_id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
def booking_health_check() -> Dict[str, str]:
    """Health check for Google Calendar booking service"""
    return {
        "status": "healthy",
        "service": "google-calendar-booking",
        "message": "Google Calendar booking service is operational"
    }
