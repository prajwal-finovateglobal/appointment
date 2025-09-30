from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from utils.config import settings

class GoogleCalendarService:
    """Service for Google Calendar operations"""
    
    def __init__(self):
        self.service = self._get_calendar_service()
    
    def _get_calendar_service(self):
        """Get authenticated Google Calendar service with write permissions"""
        SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/calendar.events'
        ]
        creds = None
        
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        return build('calendar', 'v3', credentials=creds)
    
    def check_availability(self, date_str: str, time_str: str, duration_minutes: int, timezone: str = 'Asia/Kolkata') -> Dict:
        """
        Check if a specific date/time slot is available using Google Calendar
        
        Args:
            date_str: Date in YYYY-MM-DD format
            time_str: Time in HH:MM format (24-hour)
            duration_minutes: Duration in minutes
            timezone: Timezone for the input time (default: Asia/Kolkata)
            
        Returns:
            dict with availability info
        """
        try:
            # Parse the date and time
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            # Combine date and time in the specified timezone
            tz = ZoneInfo(timezone)
            start_datetime = datetime.combine(date_obj, time_obj).replace(tzinfo=tz)
            end_datetime = start_datetime + timedelta(minutes=duration_minutes)
            
            # Convert to UTC for Google Calendar API
            start_utc = start_datetime.astimezone(ZoneInfo('UTC'))
            end_utc = end_datetime.astimezone(ZoneInfo('UTC'))
            
            # Convert to RFC3339 format for Google Calendar API
            start_rfc3339 = start_utc.isoformat().replace('+00:00', 'Z')
            end_rfc3339 = end_utc.isoformat().replace('+00:00', 'Z')
            
            # Query for events in the time range
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_rfc3339,
                timeMax=end_rfc3339,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            conflicts = len(events)
            
            return {
                "available": conflicts == 0,
                "date": date_str,
                "time": time_str,
                "duration": duration_minutes,
                "conflicts": conflicts,
                "conflicting_events": [
                    {
                        "summary": event.get('summary', 'No Title'),
                        "start": event['start'].get('dateTime', event['start'].get('date')),
                        "end": event['end'].get('dateTime', event['end'].get('date'))
                    }
                    for event in events
                ]
            }
            
        except Exception as e:
            return {
                "available": False,
                "date": date_str,
                "time": time_str,
                "duration": duration_minutes,
                "conflicts": -1,
                "error": str(e)
            }


class AvailabilityService:
    """Service for handling Google Calendar availability operations"""
    
    def __init__(self):
        try:
            self.google_calendar_service = GoogleCalendarService()
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to initialize GoogleCalendarService: {str(e)}"
            )
    
    def get_availability_for_slots(self, slots: List[Dict], timezone: str, duration_minutes: int = 60) -> Dict[str, Dict[str, Dict]]:
        """Get availability for multiple slots using Google Calendar"""
        results: Dict[str, Dict[str, Dict]] = {}
        
        for slot in slots:
            date = slot["date"]
            times = slot["times"]
            
            # Initialize day_result if it doesn't exist
            if date not in results:
                results[date] = {}
            
            # Check availability for each time slot
            for time in times:
                availability = self.google_calendar_service.check_availability(
                    date, time, duration_minutes, timezone
                )
                
                results[date][time] = {
                    "available": availability["available"],
                    "conflicts": availability["conflicts"],
                    "conflicting_events": availability.get("conflicting_events", [])
                }
        
        return results
    
    def get_free_slots_for_date_range(self, start_date: str, end_date: str, timezone: str, 
                                    duration_minutes: int = 60, working_hours: Tuple[int, int] = (9, 17)) -> Dict[str, List[str]]:
        """
        Get all free slots within a date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format  
            timezone: Timezone for the slots
            duration_minutes: Duration of each slot
            working_hours: Tuple of (start_hour, end_hour) in 24-hour format
            
        Returns:
            Dict mapping dates to lists of available time slots
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            tz = ZoneInfo(timezone)
            
            free_slots = {}
            current_date = start_dt
            
            while current_date <= end_dt:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # Get all events for this day
                day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=tz)
                day_end = day_start + timedelta(days=1)
                
                # Convert to UTC for API
                day_start_utc = day_start.astimezone(ZoneInfo('UTC'))
                day_end_utc = day_end.astimezone(ZoneInfo('UTC'))
                
                events_result = self.google_calendar_service.service.events().list(
                    calendarId='primary',
                    timeMin=day_start_utc.isoformat().replace('+00:00', 'Z'),
                    timeMax=day_end_utc.isoformat().replace('+00:00', 'Z'),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                
                events = events_result.get('items', [])
                
                # Generate working hours slots
                available_slots = []
                for hour in range(working_hours[0], working_hours[1]):
                    for minute in [0, 30]:  # 30-minute intervals
                        slot_time = f"{hour:02d}:{minute:02d}"
                        slot_datetime = datetime.combine(current_date, datetime.strptime(slot_time, '%H:%M').time()).replace(tzinfo=tz)
                        slot_end = slot_datetime + timedelta(minutes=duration_minutes)
                        
                        # Check if this slot conflicts with any events
                        conflicts = False
                        for event in events:
                            event_start = event['start'].get('dateTime', event['start'].get('date'))
                            event_end = event['end'].get('dateTime', event['end'].get('date'))
                            
                            # Parse event times
                            if 'T' in event_start:  # DateTime
                                event_start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00')).astimezone(tz)
                                event_end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00')).astimezone(tz)
                                
                                # Check for overlap
                                if (slot_datetime < event_end_dt and slot_end > event_start_dt):
                                    conflicts = True
                                    break
                            else:  # All-day event
                                conflicts = True
                                break
                        
                        if not conflicts:
                            available_slots.append(slot_time)
                
                free_slots[date_str] = available_slots
                current_date += timedelta(days=1)
            
            return free_slots
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get free slots: {str(e)}"
            )
    
    def get_events_in_date_range(self, start_date: str, end_date: str, timezone: str, calendar_id: str = None) -> List[Dict]:
        """
        Get all events within a date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            timezone: Timezone for the events
            calendar_id: Google Calendar ID
            
        Returns:
            List of event details
        """
        try:
            # Use default calendar ID if not provided
            if calendar_id is None:
                calendar_id = settings.default_calendar_id or "primary"
            
            # Parse dates and create datetime objects
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            tz = ZoneInfo(timezone)
            
            # Create start and end datetime objects
            start_datetime = datetime.combine(start_dt, datetime.min.time()).replace(tzinfo=tz)
            end_datetime = datetime.combine(end_dt, datetime.max.time()).replace(tzinfo=tz)
            
            # Convert to UTC for Google Calendar API
            start_utc = start_datetime.astimezone(ZoneInfo('UTC'))
            end_utc = end_datetime.astimezone(ZoneInfo('UTC'))
            
            # Format for Google Calendar API
            start_rfc3339 = start_utc.isoformat().replace('+00:00', 'Z')
            end_rfc3339 = end_utc.isoformat().replace('+00:00', 'Z')
            
            # Query for events in the time range
            events_result = self.google_calendar_service.service.events().list(
                calendarId=calendar_id,
                timeMin=start_rfc3339,
                timeMax=end_rfc3339,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Process events and extract relevant information
            processed_events = []
            for event in events:
                # Extract meeting link if available
                meeting_link = None
                location = event.get('location', '')
                
                # Check for Google Meet links in conferenceData (real meeting links)
                if event.get('conferenceData'):
                    entry_points = event['conferenceData'].get('entryPoints', [])
                    for entry_point in entry_points:
                        if entry_point.get('entryPointType') == 'video' and 'meet.google.com' in entry_point.get('uri', ''):
                            meeting_link = entry_point.get('uri')
                            break
                
                # Check for Google Meet links in location field (but validate they're real)
                elif location and 'meet.google.com' in location:
                    # Only use location as meeting link if it looks like a real Google Meet URL
                    if '/abc-defg-hij' not in location and len(location.split('/')[-1]) > 10:
                        meeting_link = location
                
                # Clean up location field - don't show placeholder URLs
                if location and ('abc-defg-hij' in location or 'example' in location.lower()):
                    location = None
                
                processed_event = {
                    'event_id': event['id'],
                    'title': event.get('summary', 'No Title'),
                    'start': event['start'].get('dateTime', event['start'].get('date')),
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': location,
                    'description': event.get('description'),
                    'attendees': event.get('attendees', []),
                    'meeting_link': meeting_link,
                    'status': event.get('status', 'confirmed')
                }
                processed_events.append(processed_event)
            
            return processed_events
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get events: {str(e)}"
            )
