# Healthcare Appointment & Follow-up Manager — Production Deployment Guide

## 1. Architecture Overview

The system is architected as an enterprise 12-factor cloud deployment:

```
[ Frontend: Vercel / Cloudflare Pages ]
                 │
                 ▼ HTTPS (CORS restricted)
[ Backend API: Render / Railway / AWS ECS ] <───> [ Celery Worker: Background Process ]
         │                    │                                │
         ▼                    ▼                                ▼
[ Managed PostgreSQL 16 ]   [ Managed Redis 7 ]   [ External: Gemini / GCal / SMTP ]
```

---

## 2. Production Environment Configuration

All settings are driven strictly by environment variables without hardcoded localhost fallbacks.

```env
ENVIRONMENT=production
DEBUG=False
PROJECT_NAME="Healthcare Appointment & Follow-up Manager"
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["https://healthcare-app.vercel.app"]

# PostgreSQL Database (AsyncPG connection string)
DATABASE_URL=postgresql+asyncpg://user:secure_password@postgres.provider.com:5432/healthcare_prod

# Redis Cache & Celery Broker (TLS enabled)
REDIS_URL=rediss://default:secure_redis_pass@redis.provider.com:6379/0
CELERY_BROKER_URL=rediss://default:secure_redis_pass@redis.provider.com:6379/0
CELERY_RESULT_BACKEND=rediss://default:secure_redis_pass@redis.provider.com:6379/1

# Authentication Security (Minimum 32 random characters)
SECRET_KEY=generate_a_cryptographically_secure_random_64_char_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Business Parameters
SLOT_HOLD_DURATION_MINUTES=10

# AI & LLM Provider
GEMINI_API_KEY=AIzaSy...your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash

# Google Calendar OAuth 2.0 Integration
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=https://api.yourdomain.com/api/v1/integrations/google/callback

# Transactional Email (SMTP)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_or_resend_api_key
EMAILS_FROM_EMAIL=notifications@yourdomain.com
EMAILS_FROM_NAME="Healthcare Appointment Manager"
```

---

## 3. Database Initialization & Migration

Database initialization must **never** use `Base.metadata.create_all()` in production. Run Alembic migrations:

```bash
cd backend
alembic upgrade head
```

To verify migration status:
```bash
alembic current
alembic history --verbose
```

---

## 4. Service Deployment Commands

### Backend API (Render / Railway / Fly.io / AWS)
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Pre-deploy / Release Command:** `alembic upgrade head`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4`
- **Health Check Path:** `/api/health`

### Background Celery Worker
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `celery -A app.jobs.celery_app.celery_app worker --loglevel=INFO --concurrency=4`

### Background Celery Beat Scheduler (Reminders & Hold Sweeping)
- **Root Directory:** `backend`
- **Start Command:** `celery -A app.jobs.celery_app.celery_app beat --loglevel=INFO`

### Frontend SPA (Vercel / Cloudflare Pages / Netlify)
- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variable:** `VITE_API_BASE_URL=https://api.yourdomain.com`

---

## 5. Security & Verification Checklist
1. `SECRET_KEY` is not using default development placeholder.
2. PostgreSQL connection utilizes SSL (`sslmode=require` if supported by managed provider).
3. CORS only allows the verified Vercel production frontend origin.
4. Celery worker is monitored with task retries and dead-letter handling.
5. Live health check at `GET /api/health` reports status `healthy` with low DB and Redis latency.
