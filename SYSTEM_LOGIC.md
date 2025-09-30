# 🚀 Complete Appointment System Logic Explanation

## 📋 **System Overview**
Your appointment system has **3 main components** that work together:

1. **🧠 LLM Service** - Extracts appointment data from transcripts
2. **📅 Availability Service** - Checks calendar availability 
3. **📝 Booking Service** - Creates calendar events

---

## 🧠 **1. LLM Service Logic**

### **What it does:**
- Takes customer service transcripts
- Extracts appointment information using AI
- Returns structured data for booking

### **Input:**
```json
{
  "transcript": "Hi, I'd like to schedule a meeting with John for tomorrow at 2 PM for 1 hour"
}
```

### **Processing Logic:**
1. **Parse transcript** using flexible schema
2. **Extract key information**:
   - Customer name: "John"
   - Email: From contact info
   - Date: "tomorrow" → "2025-09-30"
   - Time: "2 PM" → "14:00"
   - Duration: "1 hour" → "60 minutes"
3. **Return structured data**

### **Output:**
```json
{
  "appointments": [
    {
      "date": "2025-09-30",
      "time": "14:00",
      "duration": "60",
      "status": "offered"
    }
  ],
  "customer_name": "John",
  "contact_info": "john@example.com"
}
```

---

## 📅 **2. Availability Service Logic**

### **What it does:**
- Checks if time slots are available
- Lists all free slots in a date range
- Shows existing meetings

### **API Endpoints:**

#### **A. Batch Availability Check**
```bash
POST /availability/batch
```
**Input:**
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

**Logic:**
1. **For each slot**: Query Google Calendar API
2. **Check conflicts**: Look for existing events
3. **Return availability**: Available/conflicts/conflicting events

**Output:**
```json
{
  "results": {
    "2025-09-30": {
      "10:00": {"available": true, "conflicts": 0},
      "11:00": {"available": false, "conflicts": 1},
      "14:00": {"available": true, "conflicts": 0}
    }
  }
}
```

#### **B. Free Slots in Date Range**
```bash
POST /availability/free-slots
```
**Input:**
```json
{
  "start_date": "2025-09-30",
  "end_date": "2025-10-05",
  "working_hours": [9, 17]
}
```

**Logic:**
1. **Get all events** in date range
2. **Generate time slots** (9 AM to 5 PM, 30-min intervals)
3. **Check each slot** for conflicts
4. **Return free slots**

**Output:**
```json
{
  "free_slots": {
    "2025-09-30": ["09:00", "09:30", "14:00", "14:30"],
    "2025-10-01": ["10:00", "10:30", "15:00"]
  }
}
```

#### **C. List Existing Events**
```bash
POST /availability/events
```
**Input:**
```json
{
  "start_date": "2025-09-30",
  "end_date": "2025-10-05"
}
```

**Logic:**
1. **Query Google Calendar** for events in range
2. **Extract meeting details**: title, time, attendees, meeting links
3. **Filter out placeholder URLs** (like "abc-defg-hij")
4. **Return clean event list**

---

## 📝 **3. Booking Service Logic**

### **What it does:**
- Creates Google Calendar events
- Sends email notifications
- Generates meeting links

### **API Endpoint:**
```bash
POST /booking/create
```

### **Input (Simplified):**
```json
{
  "title": "Product Demo",
  "date": "2025-09-30",
  "time": "14:00",
  "attendee_name": "John Doe",
  "attendee_email": "john@example.com"
}
```

### **Processing Logic:**

#### **1. Environment Variables Used:**
- **Organizer Email**: From `EMAIL` env var
- **Organizer Name**: From `ORGANIZER_NAME` env var  
- **Calendar ID**: From `EMAIL` env var (same as organizer)
- **Timezone**: From `TIMEZONE` env var

#### **2. Event Creation:**
1. **Parse date/time** in specified timezone
2. **Convert to UTC** for Google Calendar API
3. **Prepare attendees list** with notification settings
4. **Create event body** with:
   - Title, description, time
   - Attendees (with responseStatus: 'needsAction')
   - Organizer details
   - Reminders (24h email, 30min popup)

#### **3. Google Meet Integration:**
- **For virtual meetings**: Auto-generate Google Meet link
- **Conference data**: Let Google create meeting room
- **Meeting link**: Extract from conferenceData

#### **4. Email Notifications:**
- **sendUpdates='all'**: Send invitations to all attendees
- **Explicit patch call**: Ensure notifications are sent
- **Response status**: Set to 'needsAction' for attendees

### **Output:**
```json
{
  "success": true,
  "event_id": "abc123",
  "event_link": "https://calendar.google.com/event?eid=...",
  "meeting_link": "https://meet.google.com/kva-ocgd-xyc",
  "message": "Booking created successfully"
}
```

---

## 🔄 **Complete Workflow Logic**

### **Step 1: Extract from Transcript**
```
Customer Call → LLM Service → Structured Data
```

### **Step 2: Check Availability**
```
Structured Data → Availability Service → Available Slots
```

### **Step 3: Book Meeting**
```
Available Slot + Customer Data → Booking Service → Calendar Event
```

### **Step 4: Notify Attendees**
```
Calendar Event → Email Notifications → Meeting Confirmation
```

---

## 🎯 **Key Features**

### **✅ Environment-Driven:**
- **One email** controls organizer and calendar
- **One timezone** used everywhere
- **Minimal API payloads**

### **✅ Smart Meeting Links:**
- **Real Google Meet** links generated
- **No placeholder URLs** in responses
- **Automatic conference data**

### **✅ Robust Availability:**
- **Multiple slot checking** (fixed the bug)
- **Date range queries**
- **Conflict detection**

### **✅ Flexible LLM:**
- **Any transcript format** accepted
- **Comprehensive extraction** (name, email, date, time, duration)
- **Confidence scoring**

---

## 🚀 **Usage Examples**

### **Complete Flow:**
```bash
# 1. Extract from transcript
POST /api/v1/extract
{
  "transcript": "Schedule meeting with John tomorrow 2 PM"
}

# 2. Check availability  
POST /availability/batch
{
  "slots": [{"date": "2025-09-30", "times": ["14:00"]}]
}

# 3. Book meeting
POST /booking/create
{
  "title": "Meeting with John",
  "date": "2025-09-30", 
  "time": "14:00",
  "attendee_name": "John",
  "attendee_email": "john@example.com"
}
```

**Your system is now complete and ready for production!** 🎉
