# Healthcare Appointment & Follow-up Manager

A production-grade full-stack healthcare appointment and clinical follow-up coordination platform built with **FastAPI**, **PostgreSQL 16**, **Redis 7**, **Celery**, **React 18**, **TypeScript**, and **Tailwind CSS**.

🚀 **Live Demo:** [Healthcare Appointment Manager](https://healthcare-appointment-manager.vercel.app/login)

---

## Key Features

- **Multi-Role Portals**: Dedicated authenticated portals for **Patients**, **Doctors**, and **Administrators** with role-based routing and RBAC enforcement.
- **Pessimistic Slot Locking & Concurrency Protection**: Zero-risk of double bookings via PostgreSQL partial unique indexes and transactional row-level locking (`SELECT ... FOR UPDATE`).
- **Temporary Slot Holds**: Configurable 10-minute hold windows with live countdown timer, allowing patients to enter symptoms before final confirmation.
- **Doctor Leave Cascading**: Automated detection of affected appointments, slot disabling, patient notification queuing, and Google Calendar event cleanup.
- **AI-Powered Pre-Visit Triage**: Gemini LLM integration generating urgency levels, chief complaints, and 3 structured triage questions (strictly non-diagnostic with safety disclaimers).
- **AI Post-Visit Summaries with Doctor Publish Gate**: Patient-friendly clinical summaries hidden from patients until explicitly reviewed and published by the doctor.
- **Google Calendar OAuth 2.0 Integration**: Doctors connect their Google Calendar to automatically sync appointment events, with non-blocking failure handling.
- **Transactional Outbox & Celery Workers**: Atomic outbox events for guaranteed email dispatch, calendar sync, and notification delivery with exponential retry.
- **Transactional Email**: Asynchronous booking confirmation, cancellation, and leave rescheduling emails via SMTP.
- **Medication Reminders**: Patient-configurable daily medication reminder scheduler.
- **69 Automated Tests**: Comprehensive test suite covering auth, booking, clinical notes, AI summaries, concurrency, security, calendar, email, and integration endpoints.

---

## Project Structure

```
healthcare-appointment-manager/
├── frontend/                     # React + TypeScript + Vite + Tailwind CSS SPA
│   ├── src/
│   │   ├── components/           # Navbar, Footer
│   │   ├── context/              # AuthContext (session & role management)
│   │   ├── pages/
│   │   │   ├── auth/             # LoginPage, RegisterPage
│   │   │   ├── patient/          # PatientDashboard (search, book, prescriptions)
│   │   │   ├── doctor/           # DoctorDashboard (clinical workspace)
│   │   │   ├── admin/            # AdminDashboard (onboarding, leaves)
│   │   │   ├── HomePage.tsx
│   │   │   ├── HealthStatusPage.tsx
│   │   │   └── ArchitectureOverviewPage.tsx
│   │   ├── services/             # Fetch-based API client (zero external deps)
│   │   ├── types/                # TypeScript type definitions
│   │   ├── App.tsx               # Root component with protected routes
│   │   └── main.tsx              # Entry point
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── backend/                      # Python FastAPI application
│   ├── app/
│   │   ├── models/               # SQLAlchemy ORM models (user, doctor, appointment, calendar, etc.)
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── routers/              # API endpoints
│   │   │   ├── health.py         # System health & diagnostics
│   │   │   ├── auth.py           # Registration, login, JWT
│   │   │   ├── doctors.py        # Doctor profiles, specializations, slots
│   │   │   ├── admin.py          # Doctor onboarding, leave management
│   │   │   ├── appointments.py   # Hold, confirm, cancel, complete
│   │   │   ├── clinical.py       # Clinical notes, prescriptions
│   │   │   ├── engagement.py     # AI summaries, notifications, reminders
│   │   │   └── integrations.py   # Google Calendar OAuth connect/callback/status/disconnect
│   │   ├── services/             # Business logic & domain services
│   │   │   ├── booking_service.py     # Concurrency-safe hold/confirm/cancel
│   │   │   ├── ai_service.py         # LLM provider with fallback
│   │   │   ├── calendar_service.py    # Google Calendar OAuth & event sync
│   │   │   ├── email_service.py       # Transactional email dispatch
│   │   │   └── leave_service.py       # Leave cascade handler
│   │   ├── jobs/                 # Celery workers & periodic tasks
│   │   ├── auth/                 # JWT & RBAC security utilities
│   │   ├── config.py             # Pydantic Settings & environment variables
│   │   ├── database.py           # Async SQLAlchemy connection & session management
│   │   └── main.py               # FastAPI app factory & lifespan handlers
│   ├── tests/                    # Pytest test suite (69 tests)
│   │   ├── test_auth.py          # 9 tests: registration, login, JWT, RBAC
│   │   ├── test_bookings.py      # 8 tests: hold, confirm, cancel, conflict
│   │   ├── test_clinical.py      # 3 tests: notes, prescriptions, authorization
│   │   ├── test_concurrency_pg.py # 2 tests: race conditions, outbox atomicity
│   │   ├── test_doctors.py       # 7 tests: profiles, specializations, working hours
│   │   ├── test_engagement.py    # 3 tests: AI summaries, publish gate, reminders
│   │   ├── test_health.py        # 4 tests: system health endpoints
│   │   ├── test_integrations.py  # 16 tests: calendar OAuth, email service, router
│   │   ├── test_security.py      # 3 tests: IDOR, role boundaries, secret key
│   │   ├── test_slots.py         # 4 tests: slot generation, idempotency, leave
│   │   ├── test_workflow.py      # 10 tests: appointment lifecycle & workflow
│   │   └── conftest.py           # Shared fixtures & test database setup
│   ├── alembic/                  # 6 database migration scripts
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── docs/                         # System documentation
│   ├── architecture.md           # System architecture & design decisions
│   ├── database-design.md        # Full schema & migration chain
│   ├── api-design.md             # REST API specification
│   ├── deployment.md             # Production deployment guide
│   ├── progress.md               # Phase completion tracking
│   └── security.md               # Security considerations
├── docker-compose.yml            # Multi-service container orchestration
├── .env.example                  # Environment variable reference template
├── .gitignore
└── README.md
```

---

## Quick Start (Local Development)

### Prerequisites
- **Python 3.12+**
- **Node.js 20+** and **npm**
- **Docker & Docker Compose** (optional, recommended for DB & Redis)

### Option 1: Running with Docker Compose (All Services)
```bash
cd healthcare-appointment-manager
cp .env.example .env
docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API Health Check: `http://localhost:8000/api/health`
- Interactive API Docs (Swagger): `http://localhost:8000/docs`

---

### Option 2: Running Services Locally

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### 3. Celery Worker (for background jobs)
```bash
cd backend
celery -A app.jobs.celery_app.celery_app worker --loglevel=INFO
```

---

## Running Tests

### Backend (69 automated tests)
```bash
cd backend
.venv\Scripts\pytest -v
```

### Frontend (production build verification)
```bash
cd frontend
npm run build
```

---

## Environment Variables

All configuration is managed via environment variables. See [`.env.example`](.env.example) and [`docs/deployment.md`](docs/deployment.md) for the complete reference.

Key variables:
| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing key (min 32 chars in production) |
| `GEMINI_API_KEY` | Google Gemini LLM API key |
| `GOOGLE_CLIENT_ID` | Google Calendar OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google Calendar OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | Transactional email configuration |
| `VITE_API_BASE_URL` | Frontend API base URL |

---

## Documentation

| Document | Description |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | System architecture, design pillars, technology stack |
| [`docs/database-design.md`](docs/database-design.md) | Full schema specification, migration chain, concurrency protocol |
| [`docs/api-design.md`](docs/api-design.md) | Complete REST API endpoint specification |
| [`docs/deployment.md`](docs/deployment.md) | Production deployment guide with cloud configuration |
| [`docs/progress.md`](docs/progress.md) | Implementation phase completion tracking |

---

## System Health

```bash
curl http://localhost:8000/api/health
```

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "services": {
    "database": { "status": "connected", "latency_ms": 1.8 },
    "redis": { "status": "connected", "latency_ms": 0.9 }
  }
}
```
