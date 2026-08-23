# Healthcare Appointment & Follow-up Manager — Testing Strategy & Verification Plan

## 1. Testing Frameworks & Philosophy

Testing is mandatory for every functional layer of the application:
- **Backend Tests**: `pytest`, `pytest-asyncio`, and `httpx.AsyncClient` ASGI transport.
- **Frontend Tests & Build Verification**: TypeScript compiler `tsc -b` and `vite build`.
- **Database & Concurrency Verification**: Real concurrent asynchronous execution tests validating serialized slot locking and HTTP 409 conflict responses.

---

## 2. Core Test Suites

### 2.1. System Health & Infrastructure Tests
- `backend/tests/test_health.py`: Verifies `/api/health`, `/api/health/db`, and `/api/health/redis`.

### 2.2. Authentication & RBAC Tests
- `backend/tests/test_auth.py`:
  - Patient registration and duplicate email rejection.
  - Login with valid vs invalid credentials.
  - `/api/v1/auth/me` identity and role verification.
  - Role restrictions (`PATIENT`, `DOCTOR`, `ADMIN`).

### 2.3. Concurrency & Double-Booking Protection Tests
- `backend/tests/test_concurrency.py`:
  - 10+ concurrent asynchronous booking requests targeting the exact same slot.
  - Verification that exactly 1 request succeeds (HTTP 200/201) and all competing requests receive `HTTP 409 Conflict`.
  - Verification that zero duplicate database rows exist.

### 2.4. Doctor Leave & Cascading Workflow Tests
- Verification that when a doctor goes on leave, overlapping confirmed/held appointments are set to `RESCHEDULED_REQUIRED` with outbox notification entries.

### 2.5. AI & External Integration Resilience Tests
- Mocked LLM timeouts and errors to guarantee core appointment bookings succeed even when external APIs fail.
