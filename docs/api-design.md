# Healthcare Appointment & Follow-up Manager — REST API Design Specification

## 1. API Conventions & Standards

- **Base URL**: `/api/v1` (with `/api/health` at root api namespace)
- **Content-Type**: `application/json`
- **Authentication**: `Bearer <JWT_TOKEN>` via HTTP `Authorization` Header
- **Standard Error Response Format**:
```json
{
  "detail": "Descriptive error message"
}
```

---

## 2. API Endpoints

### 2.1. System Health & Diagnostics

#### `GET /api/health`
Returns overall system status, uptime, environment, and connectivity status for PostgreSQL and Redis.
- **Access**: Public
- **Response 200 OK**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-08-23T22:15:00.123Z",
  "services": {
    "database": { "status": "connected", "latency_ms": 2.4 },
    "redis": { "status": "connected", "latency_ms": 1.1 }
  }
}
```

---

### 2.2. Authentication & Authorization (`/api/v1/auth`)

#### `POST /api/v1/auth/register`
- **Access**: Public (Patient registration)
- **Request**: `{ "name": "Jane Doe", "email": "patient@example.com", "password": "StrongPassword123!", "phone": "+1234567890" }`
- **Response 201 Created**: `{ "access_token": "...", "token_type": "bearer", "user": { ... } }`

#### `POST /api/v1/auth/login`
- **Access**: Public
- **Request**: `{ "email": "...", "password": "..." }`
- **Response 200 OK**: `{ "access_token": "...", "token_type": "bearer", "user": { ... } }`

#### `GET /api/v1/auth/me`
- **Access**: Authenticated (Patient / Doctor / Admin)
- **Response 200 OK**: Current user profile with role permissions.

---

### 2.3. Doctors & Availability (`/api/v1/doctors`)

#### `GET /api/v1/doctors`
- **Access**: Public / Authenticated
- **Query Params**: `specialization`, `search`
- **Response 200 OK**: List of doctor profiles.

#### `GET /api/v1/doctors/specializations`
- **Access**: Public
- **Response 200 OK**: `["Cardiology", "General Medicine", ...]`

#### `GET /api/v1/doctors/{doctor_id}`
- **Access**: Public / Authenticated
- **Response 200 OK**: Complete doctor profile.

#### `GET /api/v1/doctors/{doctor_id}/slots?date=YYYY-MM-DD`
- **Access**: Public / Authenticated
- **Response 200 OK**:
```json
{
  "doctor_id": "9d3e...",
  "date": "2026-08-25",
  "slots": [
    { "id": "...", "start_time": "2026-08-25T09:00:00Z", "end_time": "2026-08-25T09:30:00Z", "status": "available" }
  ]
}
```

#### `POST /api/v1/doctors/working-hours`
- **Access**: Authenticated (`doctor`)
- **Request**: `{ "working_hours": [{ "day_of_week": 1, "start_time": "09:00", "end_time": "17:00" }] }`

---

### 2.4. Appointments & Concurrency Engine (`/api/v1/appointments`)

#### `POST /api/v1/appointments/hold`
Acquires a temporary lock on a slot before symptom entry and confirmation.
- **Access**: Authenticated (`patient`)
- **Request**: `{ "slot_id": "..." }`
- **Response 201 Created**: Hold record with `expires_at`
- **Response 409 Conflict**: Slot already held or booked.

#### `POST /api/v1/appointments/{hold_id}/confirm`
Confirms the held slot and creates the appointment.
- **Access**: Authenticated (`patient`)
- **Request**: `{ "chief_complaint": "..." }`
- **Response 200 OK**: Confirmed appointment record.

#### `POST /api/v1/appointments/holds/{hold_id}/release`
Releases a temporary hold, making the slot available again.
- **Access**: Authenticated (`patient`)
- **Response 200 OK**: Released hold record.

#### `POST /api/v1/appointments/{id}/cancel`
- **Access**: Authenticated (`patient`, `doctor`, `admin`)
- **Request**: `{ "reason": "Patient conflict" }`
- **Response 200 OK**: Cancelled appointment + triggered calendar deletion + patient email.

#### `POST /api/v1/appointments/{id}/complete`
- **Access**: Authenticated (`doctor`)
- **Response 200 OK**: Completed appointment.

#### `POST /api/v1/appointments/{id}/reschedule-required`
- **Access**: Authenticated (`doctor`)
- **Response 200 OK**: Appointment marked for rescheduling.

#### `GET /api/v1/appointments/me`
- **Access**: Authenticated (`patient` or `doctor`)
- **Query Params**: `appointment_status`
- **Response 200 OK**: List of appointments.

---

### 2.5. Clinical Notes & Prescriptions (`/api/v1/clinical`)

#### `PUT /api/v1/clinical/appointments/{appointment_id}/note`
- **Access**: Authenticated (`doctor`)
- **Request**: `{ "content": "Clinical observations..." }`
- **Response 200 OK**: Upserted clinical note.

#### `POST /api/v1/clinical/appointments/{appointment_id}/prescriptions`
- **Access**: Authenticated (`doctor`)
- **Request**: `{ "medication_name": "Ibuprofen 400mg", "dosage": "1 tablet", "frequency": "Every 8 hours", "instructions": "Take with food" }`
- **Response 201 Created**: Prescription record.

#### `GET /api/v1/clinical/prescriptions/me`
- **Access**: Authenticated (`patient`)
- **Response 200 OK**: List of patient's prescriptions.

---

### 2.6. AI Engagement & Notifications (`/api/v1/engagement`)

#### `POST /api/v1/engagement/appointments/{id}/pre-visit-summary`
- **Access**: Authenticated (`patient`)
- **Request**: `{ "symptoms": "..." }`
- **Response 200 OK**: `{ "urgency": "Medium", "chief_complaint": "...", "suggested_questions": ["..."], "disclaimer": "..." }`

#### `POST /api/v1/engagement/appointments/{id}/post-visit-summary`
- **Access**: Authenticated (`doctor`)
- **Request**: `{ "follow_up_instructions": "..." }`
- **Response 200 OK**: AI-generated draft summary (unpublished).

#### `POST /api/v1/engagement/post-visit-summaries/{id}/publish`
- **Access**: Authenticated (`doctor`)
- **Response 200 OK**: Summary marked as published, now visible to patient.

#### `GET /api/v1/engagement/appointments/{id}/post-visit-summary`
- **Access**: Authenticated (`patient`)
- **Response 200 OK**: Published post-visit summary (returns 404 if not yet published).

#### `GET /api/v1/engagement/notifications/me`
- **Access**: Authenticated
- **Response 200 OK**: List of in-app notifications.

#### `POST /api/v1/engagement/reminders`
- **Access**: Authenticated (`patient`)
- **Request**: `{ "prescription_id": "...", "schedule": { "times": ["08:00", "20:00"] } }`
- **Response 201 Created**: Medication reminder configured.

#### `GET /api/v1/engagement/reminders/me`
- **Access**: Authenticated (`patient`)
- **Response 200 OK**: List of active medication reminders.

---

### 2.7. Admin Management (`/api/v1/admin`)

#### `POST /api/v1/admin/doctors`
- **Access**: Authenticated (`admin`)
- **Request**: `{ "name": "...", "email": "...", "password": "...", "specialization": "...", "slot_duration_minutes": 30, "consultation_fee": 100 }`
- **Response 201 Created**: Doctor user account and profile.

#### `GET /api/v1/admin/doctors`
- **Access**: Authenticated (`admin`)
- **Response 200 OK**: List of all doctor profiles.

#### `PUT /api/v1/admin/doctors/{doctor_id}`
- **Access**: Authenticated (`admin`)
- **Request**: Update doctor specialization, bio, slot duration.

#### `POST /api/v1/admin/doctors/{doctor_id}/working-hours`
- **Access**: Authenticated (`admin`)
- **Request**: Set weekly working shifts.

#### `POST /api/v1/admin/leaves`
- **Access**: Authenticated (`admin`)
- **Request**: `{ "doctor_id": "...", "leave_date": "2026-09-01", "end_date": "2026-09-05", "reason": "Annual Conference" }`
- **Response 201 Created**: Leave record with cascaded slot and appointment impact.

#### `GET /api/v1/admin/leaves`
- **Access**: Authenticated (`admin`)
- **Query Params**: `doctor_id`
- **Response 200 OK**: List of all leaves.

#### `DELETE /api/v1/admin/leaves/{leave_id}`
- **Access**: Authenticated (`admin`)
- **Response 200 OK**: Leave cancelled.

---

### 2.8. Google Calendar Integration (`/api/v1/integrations/google`)

#### `GET /api/v1/integrations/google/connect`
- **Access**: Authenticated (`doctor`)
- **Response 200 OK**: `{ "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...", "message": "Redirect the user to this URL..." }`

#### `GET /api/v1/integrations/google/callback`
- **Access**: Public (redirected from Google)
- **Query Params**: `code` (authorization code), `state` (doctor UUID)
- **Response 200 OK**: `{ "message": "Google Calendar connected successfully.", "doctor_id": "...", "calendar_id": "primary", "is_connected": true }`
- **Response 400 Bad Request**: Invalid state parameter.

#### `GET /api/v1/integrations/google/status`
- **Access**: Authenticated (`doctor`)
- **Response 200 OK**:
```json
{
  "is_connected": true,
  "calendar_id": "primary",
  "last_updated": "2026-08-24T10:30:00Z",
  "recent_syncs": [
    {
      "appointment_id": "...",
      "google_event_id": "gcal_abc123",
      "sync_status": "synced",
      "last_synced_at": "2026-08-24T10:30:00Z",
      "error_message": null
    }
  ]
}
```

#### `DELETE /api/v1/integrations/google/disconnect`
- **Access**: Authenticated (`doctor`)
- **Response 200 OK**: `{ "message": "Google Calendar disconnected.", "doctor_id": "..." }`
