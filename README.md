# 🚀 Appointment Extraction & Booking System

A complete AI-powered appointment system that extracts meeting details from customer service transcripts and automatically books Google Calendar events.

## ✨ Features

- **AI-Powered Extraction**: Uses OpenAI LLM to extract appointment details from any transcript format
- **Google Calendar Integration**: Check availability and book meetings automatically
- **Environment-Driven**: Configure once, use everywhere
- **RESTful API**: Clean, simple API endpoints
- **Smart Meeting Links**: Real Google Meet links, no placeholders
- **Flexible Schema**: Handles any transcript format (timestamp, sender, text)

## 🏗️ System Architecture

```
Customer Transcript → LLM Service → Availability Check → Booking Service → Google Calendar
```

### Core Components:
1. **LLM Service**: Extracts name, email, date, time, duration from transcripts
2. **Availability Service**: Checks calendar slots, lists free times, shows existing events
3. **Booking Service**: Creates Google Calendar events with email notifications

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud Project with Calendar API enabled
- OpenAI API key

### 1. Clone & Setup
```bash
git clone <your-repo>
cd appointment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Create `.env` file:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google Calendar Configuration  
EMAIL=your_email@example.com
ORGANIZER_NAME=Name
TIMEZONE=Asia/Kolkata

PAT=your_personal_access_token_here

# Optional: Custom settings
OPENAI_MODEL=gpt-4.1-mini-2025-04-14
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### 3. Google Calendar Setup
1. **Enable Google Calendar API** in Google Cloud Console
2. **Create OAuth credentials** (`credentials.json`)
3. **Run authentication** (first time only):
   ```bash
   python -c "from services.google_calendar_booking_service import GoogleCalendarBookingService; GoogleCalendarBookingService()"
   ```
4. **Follow OAuth flow** in browser
5. **Token saved** automatically for future use

### 4. Run the Application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test the API
```bash
# Health check
curl http://localhost:8000/health

# Extract appointments from transcript
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hi, I want to schedule a meeting with John tomorrow at 2 PM for 1 hour",
    "session_id": "test-123"
  }'
```

## 📚 API Documentation

### 🧠 LLM Service - Extract Appointments

**Endpoint**: `POST /api/v1/extract`

**Request**:
```json
{
  "transcript": "Schedule meeting with John tomorrow 2 PM for 1 hour",
  "session_id": "optional-session-id"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "appointments": [
      {
        "date": "2025-09-30",
        "time": "14:00", 
        "duration": "60",
        "status": "offered",
        "event_name": "Meeting"
      }
    ],
    "customer_name": "John",
    "contact_info": "john@example.com",
    "confidence_score": 0.85
  }
}
```

### 📅 Availability Service

#### Check Multiple Slots
**Endpoint**: `POST /availability/batch`

**Request**:
```json
{
  "timezone": "Asia/Kolkata",
  "duration_minutes": 60,
  "slots": [
    {
      "date": "2025-09-30",
      "times": ["10:00", "11:00", "14:00"]
    }
  ]
}
```

#### Get Free Slots in Date Range
**Endpoint**: `POST /availability/free-slots`

**Request**:
```json
{
  "start_date": "2025-09-30",
  "end_date": "2025-10-05",
  "working_hours": [9, 17]
}
```

#### List Existing Events
**Endpoint**: `POST /availability/events`

**Request**:
```json
{
  "start_date": "2025-09-30",
  "end_date": "2025-10-05"
}
```

### 📝 Booking Service

**Endpoint**: `POST /booking/create`

**Request**:
```json
{
  "title": "Product Demo Meeting",
  "date": "2025-09-30",
  "time": "14:00",
  "attendee_name": "John Doe",
  "attendee_email": "john@example.com",
  "duration_minutes": 60
}
```

**Response**:
```json
{
  "success": true,
  "event_id": "abc123",
  "event_link": "https://calendar.google.com/event?eid=...",
  "meeting_link": "https://meet.google.com/kva-ocgd-xyc",
  "message": "Booking created successfully"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default Value |
|----------------------|-------------|---------------|
| `OPENAI_API_KEY`     | API key for OpenAI services | Required |
| `EMAIL`              | Email and calendar ID of the organizer | Required |
| `ORGANIZER_NAME`     | Display name of the organizer | "Meeting Organizer" |
| `TIMEZONE`           | Default time zone for scheduling | "Asia/Kolkata" |
| `OPENAI_MODEL`       | Model version used for OpenAI | "gpt-4.1-mini-2025-04-14" |
| `API_HOST`           | Host address for the server | "0.0.0.0" |
| `API_PORT`           | Port number for the server | 8000 |
| `DEBUG`              | Enable or disable debug mode | true |

### Google Calendar Setup

1. **Create Google Cloud Project**
2. **Enable Calendar API**
3. **Create OAuth 2.0 credentials**
4. **Download `credentials.json`**
5. **Run authentication flow** (one-time setup)

## 🏃‍♂️ Complete Workflow Example

```bash
# 1. Extract appointment from transcript
curl -X POST "http://localhost:8000/api/v1/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hi, I need to schedule a product demo with Sarah next Tuesday at 3 PM for 2 hours"
  }'

# 2. Check availability for the suggested time
curl -X POST "http://localhost:8000/availability/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "slots": [
      {
        "date": "2025-10-01",
        "times": ["15:00"]
      }
    ]
  }'

# 3. Book the meeting
curl -X POST "http://localhost:8000/booking/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Demo",
    "date": "2025-10-01",
    "time": "15:00",
    "attendee_name": "Sarah",
    "attendee_email": "sarah@example.com",
    "duration_minutes": 120
  }'
```

## 🐛 Troubleshooting

### Common Issues

1. **"Authentication failed"**
   - Check `credentials.json` exists
   - Run OAuth flow again
   - Verify Google Calendar API is enabled

2. **"No service account credentials found"**
   - Use OAuth flow (not service account)
   - Ensure `token.json` is generated

3. **"Import errors"**
   - Install missing packages: `pip install google-auth google-auth-oauthlib google-api-python-client`

4. **"Calendar not found"**
   - Check `EMAIL` environment variable
   - Verify calendar sharing permissions

## 📁 Project Structure

```
appointment/
├── api/                    # API endpoints
│   ├── availability.py     # Availability endpoints
│   ├── booking.py         # Booking endpoints
│   └── endpoints.py       # Main API endpoints
├── models/                 # Pydantic models
│   ├── appointment.py     # Appointment models
│   ├── availability.py    # Availability models
│   ├── booking.py         # Booking models
│   └── transcript.py      # Transcript models
├── services/              # Business logic
│   ├── llm_service.py     # OpenAI LLM service
│   ├── availability_service.py  # Calendar availability
│   ├── google_calendar_booking_service.py  # Booking service
│   └── rag_service.py    # RAG processing
├── utils/                 # Utilities
│   ├── config.py         # Configuration
│   └── text_processing.py # Text processing
├── main.py               # FastAPI application
├── requirements.txt      # Dependencies
├── .env                  # Environment variables
├── credentials.json      # Google OAuth credentials
└── token.json           # OAuth tokens (auto-generated)
```


