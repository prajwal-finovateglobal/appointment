# Google Calendar Booking & Availability API

A streamlined Google Calendar integration API for booking meetings and checking availability with centralized authentication.

## 🚀 Features

- **Google Calendar Integration**: Book meetings and check availability
- **Centralized Authentication**: Persistent OAuth2 authentication with automatic token refresh
- **Simplified API**: Clean, minimal endpoints for booking and availability
- **Real Google Meet Links**: Automatic Google Meet conference creation
- **Flexible Attendee Management**: Support for multiple attendees with structured data
- **Timezone Support**: Full timezone handling for global scheduling

## 📋 API Endpoints

### Booking Service
- `POST /booking/create` - Create a new meeting
- `PUT /booking/update` - Update existing meeting
- `DELETE /booking/cancel` - Cancel a meeting
- `GET /booking/details/{event_id}` - Get meeting details
- `GET /booking/health` - Health check

### Availability Service
- `POST /availability/batch` - Check multiple time slots
- `POST /availability/free-slots` - Get free slots in date range
- `POST /availability/events` - List existing events
- `GET /availability/health` - Health check

## 🛠️ Quick Start

### 1. Prerequisites
- Python 3.11+
- Google Cloud Project with Calendar API enabled
- Google OAuth2 credentials

### 2. Installation
```bash
git clone <your-repo>
cd appointment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Setup
Create `.env` file:
```env
# Google Calendar Configuration
EMAIL=your_email@example.com
ORGANIZER_NAME=Your Name
TIMEZONE=Asia/Kolkata

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### 4. Google Calendar Authentication
1. **Enable Google Calendar API** in Google Cloud Console
2. **Create OAuth credentials** and download as `credentials.json`
3. **Place `credentials.json`** in the project root
4. **Run the app** - authentication will be handled automatically

### 5. Run the Application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📖 API Usage Examples

### Create a Meeting
```bash
curl -X POST "http://localhost:8000/booking/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Demo Meeting",
    "description": "Product demonstration and Q&A session",
    "date": "2025-10-13",
    "time": "14:00",
    "duration_minutes": 60,
    "timezone": "Asia/Kolkata",
    "all_attendees": [
      {
        "name": "John Doe",
        "email": "john@example.com"
      }
    ],
    "location": {
      "type": "virtual"
    },
    "meeting_notes": "Please prepare demo materials",
    "send_notifications": true,
    "calendar_id": "primary",
    "visibility": "default"
  }'
```

### Check Availability
```bash
curl -X POST "http://localhost:8000/availability/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "timezone": "Asia/Kolkata",
    "duration_minutes": 60,
    "slots": [
      {
        "date": "2025-10-13",
        "times": ["10:00", "11:00", "14:00"]
      }
    ]
  }'
```

### Get Free Slots
```bash
curl -X POST "http://localhost:8000/availability/free-slots" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-13",
    "end_date": "2025-10-15",
    "timezone": "Asia/Kolkata",
    "duration_minutes": 60,
    "working_hours": [9, 17]
  }'
```

### List Existing Events
```bash
curl -X POST "http://localhost:8000/availability/events" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-10-13",
    "end_date": "2025-10-15",
    "timezone": "Asia/Kolkata",
    "calendar_id": "primary"
  }'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL` | Google Calendar email/ID | Required |
| `ORGANIZER_NAME` | Display name for organizer | "Meeting Organizer" |
| `TIMEZONE` | Default timezone | "Asia/Kolkata" |
| `API_HOST` | Server host | "0.0.0.0" |
| `API_PORT` | Server port | 8000 |
| `DEBUG` | Debug mode | true |

### Google Calendar Setup

1. **Google Cloud Console**:
   - Create/select project
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials
   - Download `credentials.json`

2. **Authentication**:
   - Place `credentials.json` in project root
   - First run will open browser for OAuth
   - Tokens are automatically saved and refreshed

## 📁 Project Structure

```
appointment/
├── api/                           # API endpoints
│   ├── booking.py                 # Booking endpoints
│   └── availability.py           # Availability endpoints
├── models/                        # Pydantic models
│   ├── booking.py                 # Booking models
│   └── availability.py            # Availability models
├── services/                        # Business logic
│   ├── auth.py                    # Centralized authentication
│   ├── google_calendar_booking_service.py  # Booking service
│   └── availability_service.py    # Availability service
├── utils/                         # Utilities
│   └── config.py                  # Configuration
├── main.py                        # FastAPI application
├── requirements.txt               # Dependencies
├── credentials.json              # Google OAuth credentials
└── README.md                     # This file
```

## 🔐 Authentication System

The API uses a centralized authentication system (`services/auth.py`) that:

- **Automatically handles OAuth2 flow** on first run
- **Persists credentials** for future use
- **Refreshes tokens** automatically when expired
- **Provides unified authentication** across all services

## 📊 Response Examples

### Booking Response
```json
{
  "success": true,
  "event_id": "abc123def456",
  "event_link": "https://calendar.google.com/event?eid=...",
  "meeting_link": "https://meet.google.com/kva-ocgd-xyc",
  "event_details": {
    "title": "Product Demo Meeting",
    "start": "2025-10-13T14:00:00+05:30",
    "end": "2025-10-13T15:00:00+05:30"
  },
  "message": "Booking created successfully. Notifications: sent",
  "calendar_info": {
    "provider": "Google Calendar",
    "calendar_id": "primary"
  }
}
```

### Availability Response
```json
{
  "timezone": "Asia/Kolkata",
  "duration_minutes": 60,
  "results": {
    "2025-10-13": {
      "10:00": {
        "available": true,
        "conflicts": 0,
        "conflicting_events": []
      },
      "11:00": {
        "available": false,
        "conflicts": 1,
        "conflicting_events": [
          {
            "summary": "Existing Meeting",
            "start": "2025-10-13T11:00:00+05:30",
            "end": "2025-10-13T12:00:00+05:30"
          }
        ]
      }
    }
  },
  "calendar_info": {
    "provider": "Google Calendar",
    "calendar_id": "primary"
  }
}
```

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Error**:
   - Ensure `credentials.json` exists in project root
   - Check Google Calendar API is enabled
   - Verify OAuth credentials are correct

2. **Import Errors**:
   - Install dependencies: `pip install -r requirements.txt`
   - Check Python version (3.11+)

3. **Calendar Access**:
   - Verify `EMAIL` environment variable
   - Check calendar sharing permissions
   - Ensure OAuth scopes include calendar access

## 🎯 Key Features

- **Simplified API**: Only essential parameters required
- **Automatic Authentication**: No manual token management
- **Real Google Meet**: No placeholder links
- **Timezone Aware**: Proper timezone handling
- **Error Handling**: Comprehensive error responses
- **Health Checks**: Service monitoring endpoints

## 📝 License

This project is part of the appointment booking system.