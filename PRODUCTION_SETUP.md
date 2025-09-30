# Production Google Calendar Authentication Setup

## Quick Setup Guide

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Google Calendar API

### 2. Create Service Account
1. Go to IAM & Admin > Service Accounts
2. Click "Create Service Account"
3. Name: `calendar-booking-service`
4. Description: `Service account for calendar booking operations`
5. Click "Create and Continue"
6. Grant roles: **Skip this step for now** (we'll configure permissions later)
7. Click "Done"

### 3. Generate Credentials (Keys)
**⚠️ Organization Policy Note**: If you see "An organisation policy that blocks service account key creation has been enforced", use the alternatives below instead.

#### Option A: Try to Create Keys (if allowed)
1. Click on the created service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" format
5. Click "Create"
6. Download the JSON file

#### Option B: Use Workload Identity (RECOMMENDED for Production)
If service account keys are blocked, use Application Default Credentials:

1. **No JSON file needed**
2. **Set up Workload Identity** in your cloud environment
3. **Use the service account email** for calendar sharing
4. **The service will automatically use Workload Identity**

#### Option C: Use OAuth for Development
For local development when keys are blocked:

1. **Create OAuth credentials** instead of service account keys
2. **Use the existing OAuth flow** in your current service
3. **This works for development/testing**

### 4. Configure Environment Variables

#### Option A: JSON File
```bash
# Place the downloaded JSON file in your project
cp ~/Downloads/service-account-credentials.json ./service-account-credentials.json
```

#### Option B: Environment Variable (Recommended for Production)
```bash
# Set the entire JSON as environment variable
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"your-project",...}'
```

#### Option C: Google Application Default Credentials
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-credentials.json"
```

### 5. Share Calendar (Important!)
1. Go to Google Calendar
2. Share your calendar with the service account email
3. Grant "Make changes to events" permission

### 6. Alternative: Configure IAM Roles (Optional)
If you want to grant broader permissions to the service account:

1. Go to IAM & Admin > IAM
2. Find your service account
3. Click "Edit" (pencil icon)
4. Click "Add Another Role"
5. Search for and add these roles:
   - `Service Account User` (basic role)
   - `Calendar API User` (if available)
   - Or create custom role with these permissions:
     - `calendar.events.create`
     - `calendar.events.update`
     - `calendar.events.delete`
     - `calendar.events.get`
     - `calendar.calendars.get`

### 7. Update Your Code
Replace the current booking service with the production version:

```python
# In your API endpoints
from services.production_google_calendar_booking_service import ProductionGoogleCalendarBookingService

# Use the production service
booking_service = ProductionGoogleCalendarBookingService()
```

### 8. Docker/Production Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set environment variable for credentials
ENV GOOGLE_SERVICE_ACCOUNT_JSON=""

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
version: '3.8'
services:
  appointment-api:
    build: .
    environment:
      - GOOGLE_SERVICE_ACCOUNT_JSON=${GOOGLE_SERVICE_ACCOUNT_JSON}
    ports:
      - "8000:8000"
```

### 9. Security Best Practices
- ✅ Never commit credentials to version control
- ✅ Use secrets management in production
- ✅ Rotate service account keys regularly
- ✅ Use least privilege principle
- ✅ Monitor API usage

### 10. Testing
```bash
# Test the service
python -c "from services.production_google_calendar_booking_service import ProductionGoogleCalendarBookingService; print('✅ Production service ready!')"
```

## Benefits of Service Account Approach
- ✅ No user interaction required
- ✅ Works in production environments
- ✅ Can be automated and scaled
- ✅ Secure credential management
- ✅ No token refresh needed
- ✅ Perfect for server-to-server communication
