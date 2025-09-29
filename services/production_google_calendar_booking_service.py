from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

from models.booking import (
    GoogleCalendarBookingRequest, 
    GoogleCalendarBookingResponse,
    BookingUpdateRequest,
    BookingCancellationRequest,
    MeetingLocation
)


class ProductionGoogleCalendarBookingService:
    """Production-ready Google Calendar booking service using Service Account authentication"""
    
    def __init__(self):
        self.service = self._get_calendar_service()
    
    def _get_calendar_service(self):
        """Get authenticated Google Calendar service using multiple authentication methods"""
        SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        
        try:
            # Method 1: Service Account File (if available)
            if os.path.exists('service-account-credentials.json'):
                credentials = service_account.Credentials.from_service_account_file(
                    'service-account-credentials.json', scopes=SCOPES
                )
                print("✅ Using service account file authentication")
            
            # Method 2: Environment Variable (JSON string)
            elif os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'):
                service_account_info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info, scopes=SCOPES
                )
                print("✅ Using service account environment variable authentication")
            
            # Method 3: Google Application Default Credentials (Workload Identity)
            elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
                credentials = service_account.Credentials.from_service_account_file(
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'], scopes=SCOPES
                )
                print("✅ Using Google Application Default Credentials")
            
            # Method 4: Application Default Credentials (for production/cloud)
            else:
                from google.auth import default
                credentials, project = default(scopes=SCOPES)
                print("✅ Using Application Default Credentials (Workload Identity)")
            
            # Optional: Domain-wide delegation (impersonate a user)
            if os.environ.get('GOOGLE_IMPERSONATE_USER'):
                credentials = credentials.with_subject(os.environ['GOOGLE_IMPERSONATE_USER'])
                print(f"✅ Impersonating user: {os.environ['GOOGLE_IMPERSONATE_USER']}")
            
            return build('calendar', 'v3', credentials=credentials)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Authentication failed: {str(e)}. Please check your credentials configuration."
            )
    
    def create_booking(self, request: GoogleCalendarBookingRequest) -> GoogleCalendarBookingResponse:
        """Create a new Google Calendar event/booking"""
        try:
            # Parse date and time
            date_obj = datetime.strptime(request.date, '%Y-%m-%d')
            time_obj = datetime.strptime(request.time, '%H:%M').time()
            
            # Combine date and time in the specified timezone
            tz = ZoneInfo(request.timezone)
            start_datetime = datetime.combine(date_obj, time_obj).replace(tzinfo=tz)
            end_datetime = start_datetime + timedelta(minutes=request.duration_minutes)
            
            # Convert to UTC for Google Calendar API
            start_utc = start_datetime.astimezone(ZoneInfo('UTC'))
            end_utc = end_datetime.astimezone(ZoneInfo('UTC'))
            
            # Format for Google Calendar API
            start_rfc3339 = start_utc.isoformat().replace('+00:00', 'Z')
            end_rfc3339 = end_utc.isoformat().replace('+00:00', 'Z')
            
            # Prepare attendees list with proper notification settings
            attendees = []
            
            # Handle different attendee input formats
            if request.all_attendees:
                # Use structured attendee list if provided
                for attendee in request.all_attendees:
                    attendees.append({
                        'email': attendee.email,
                        'displayName': attendee.name,
                        'responseStatus': 'needsAction'
                    })
            else:
                # Use traditional format (primary + additional)
                attendees.append({
                    'email': request.attendee_email, 
                    'displayName': request.attendee_name,
                    'responseStatus': 'needsAction'
                })
                
                if request.additional_attendees:
                    for email in request.additional_attendees:
                        attendees.append({
                            'email': email,
                            'responseStatus': 'needsAction'
                        })
            
            # Prepare event body
            event_body = {
                'summary': request.title,
                'description': request.description or '',
                'start': {
                    'dateTime': start_rfc3339,
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': end_rfc3339,
                    'timeZone': 'UTC'
                },
                'attendees': attendees,
                'organizer': {
                    'email': request.organizer_email,
                    'displayName': request.organizer_name
                },
                'visibility': request.visibility,
                'guestsCanModify': False,
                'guestsCanInviteOthers': False,
                'guestsCanSeeOtherGuests': True,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'popup', 'minutes': 30}        # 30 minutes before
                    ]
                }
            }
            
            # Add location if provided
            if request.location:
                if request.location.type == 'virtual':
                    # Always create Google Meet link for virtual meetings
                    event_body['conferenceData'] = {
                        'createRequest': {
                            'requestId': f"meet-{datetime.now().timestamp()}",
                            'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                        }
                    }
                    # Don't set custom meeting link as location - let Google generate the real one
                    # Custom links should be used for external meeting platforms, not Google Meet
                    if request.location.meeting_link and not request.location.meeting_link.startswith('https://meet.google.com/'):
                        # Only use custom link if it's NOT a Google Meet link
                        event_body['location'] = request.location.meeting_link
                elif request.location.type == 'physical' and request.location.address:
                    event_body['location'] = request.location.address
                elif request.location.type == 'phone' and request.location.phone_number:
                    event_body['location'] = f"Phone: {request.location.phone_number}"
            
            # Add meeting notes to description
            if request.meeting_notes:
                if event_body['description']:
                    event_body['description'] += f"\n\nMeeting Notes: {request.meeting_notes}"
                else:
                    event_body['description'] = f"Meeting Notes: {request.meeting_notes}"
            
            # Create the event
            created_event = self.service.events().insert(
                calendarId=request.calendar_id,
                body=event_body,
                conferenceDataVersion=1 if request.location and request.location.type == 'virtual' else 0,
                sendUpdates='all' if request.send_notifications else 'none'
            ).execute()
            
            # Extract meeting link if it's a virtual meeting
            meeting_link = None
            if created_event.get('conferenceData'):
                meeting_link = created_event['conferenceData'].get('entryPoints', [{}])[0].get('uri')
            
            # If notifications are enabled, explicitly send invitations
            if request.send_notifications:
                try:
                    # Send explicit invitations to ensure attendees get notified
                    self.service.events().patch(
                        calendarId=request.calendar_id,
                        eventId=created_event['id'],
                        body={'attendees': attendees},
                        sendUpdates='all'
                    ).execute()
                except Exception as e:
                    # Log the error but don't fail the booking
                    print(f"Warning: Failed to send explicit invitations: {e}")
            
            return GoogleCalendarBookingResponse(
                success=True,
                event_id=created_event['id'],
                event_link=created_event.get('htmlLink', ''),
                meeting_link=meeting_link,
                event_details={
                    'summary': created_event.get('summary'),
                    'start': created_event.get('start'),
                    'end': created_event.get('end'),
                    'attendees': created_event.get('attendees', []),
                    'location': meeting_link if meeting_link else created_event.get('location'),
                    'description': created_event.get('description')
                },
                message=f"Booking created successfully. Notifications: {'sent' if request.send_notifications else 'disabled'}"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create booking: {str(e)}"
            )
    
    def update_booking(self, request: BookingUpdateRequest) -> GoogleCalendarBookingResponse:
        """Update an existing Google Calendar event/booking"""
        try:
            # Get the existing event
            existing_event = self.service.events().get(
                calendarId='primary',
                eventId=request.event_id
            ).execute()
            
            # Update fields if provided
            if request.title:
                existing_event['summary'] = request.title
            if request.description:
                existing_event['description'] = request.description
            if request.date and request.time:
                # Parse new date and time
                date_obj = datetime.strptime(request.date, '%Y-%m-%d')
                time_obj = datetime.strptime(request.time, '%H:%M').time()
                
                # Get timezone from existing event
                existing_start = existing_event['start'].get('dateTime')
                if existing_start:
                    tz = ZoneInfo('UTC')  # Default to UTC, could be improved
                    start_datetime = datetime.combine(date_obj, time_obj).replace(tzinfo=tz)
                    end_datetime = start_datetime + timedelta(minutes=request.duration_minutes or 60)
                    
                    start_utc = start_datetime.astimezone(ZoneInfo('UTC'))
                    end_utc = end_datetime.astimezone(ZoneInfo('UTC'))
                    
                    existing_event['start'] = {
                        'dateTime': start_utc.isoformat().replace('+00:00', 'Z'),
                        'timeZone': 'UTC'
                    }
                    existing_event['end'] = {
                        'dateTime': end_utc.isoformat().replace('+00:00', 'Z'),
                        'timeZone': 'UTC'
                    }
            
            if request.location:
                if request.location.type == 'virtual' and request.location.meeting_link:
                    existing_event['location'] = request.location.meeting_link
                elif request.location.type == 'physical' and request.location.address:
                    existing_event['location'] = request.location.address
                elif request.location.type == 'phone' and request.location.phone_number:
                    existing_event['location'] = f"Phone: {request.location.phone_number}"
            
            if request.meeting_notes:
                if existing_event.get('description'):
                    existing_event['description'] += f"\n\nUpdated Notes: {request.meeting_notes}"
                else:
                    existing_event['description'] = f"Updated Notes: {request.meeting_notes}"
            
            # Update send notifications setting
            existing_event['sendUpdates'] = 'all' if request.send_notifications else 'none'
            
            # Update the event
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=request.event_id,
                body=existing_event
            ).execute()
            
            return GoogleCalendarBookingResponse(
                success=True,
                event_id=updated_event['id'],
                event_link=updated_event.get('htmlLink', ''),
                meeting_link=updated_event.get('conferenceData', {}).get('entryPoints', [{}])[0].get('uri'),
                event_details={
                    'summary': updated_event.get('summary'),
                    'start': updated_event.get('start'),
                    'end': updated_event.get('end'),
                    'attendees': updated_event.get('attendees', []),
                    'location': updated_event.get('location'),
                    'description': updated_event.get('description')
                },
                message="Booking updated successfully"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update booking: {str(e)}"
            )
    
    def cancel_booking(self, request: BookingCancellationRequest) -> Dict[str, Any]:
        """Cancel a Google Calendar event/booking"""
        try:
            # Delete the event
            self.service.events().delete(
                calendarId='primary',
                eventId=request.event_id,
                sendUpdates='all' if request.send_notifications else 'none'
            ).execute()
            
            return {
                "success": True,
                "event_id": request.event_id,
                "message": "Booking cancelled successfully",
                "reason": request.reason
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to cancel booking: {str(e)}"
            )
    
    def get_booking_details(self, event_id: str) -> Dict[str, Any]:
        """Get details of a specific booking"""
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            return {
                "success": True,
                "event_id": event_id,
                "event_details": {
                    'summary': event.get('summary'),
                    'start': event.get('start'),
                    'end': event.get('end'),
                    'attendees': event.get('attendees', []),
                    'location': event.get('location'),
                    'description': event.get('description'),
                    'status': event.get('status'),
                    'htmlLink': event.get('htmlLink')
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get booking details: {str(e)}"
            )
