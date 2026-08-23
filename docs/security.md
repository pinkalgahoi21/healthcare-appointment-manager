# Healthcare Appointment & Follow-up Manager — Security Architecture & Guidelines

## 1. Security Overview

The platform is designed with healthcare-grade security principles, strict role isolation, zero-trust access control, and defense-in-depth data protection.

---

## 2. Core Security Controls

### 2.1. Authentication & Session Management
- **Stateless JWT Tokens**: Signed with `HMAC-SHA256` using secure, environment-injected secret keys (`SECRET_KEY`).
- **Token Expiration**: Configurable lifetime (default 60 minutes).
- **Password Security**: Passwords hashed using `bcrypt` (work factor 12) with unique per-user salts. Plaintext passwords are never logged, stored, or transmitted in responses.

### 2.2. Role-Based Access Control (RBAC) & IDOR Protection
Three discrete system roles with explicit least-privilege permissions:
- **PATIENT**: Can only access their own appointments, prescriptions, reminders, and approved post-visit summaries. Cannot access another patient's records or doctor-only endpoints.
- **DOCTOR**: Can access appointments assigned to them, patient symptom briefings, and draft clinical notes/prescriptions. Cannot view unrelated patients or modify clinic-wide administrative settings.
- **ADMIN**: Can manage doctor profiles, working hours, slot parameters, and doctor leave calendars.

Every protected API route performs:
1. Token validation & user identity resolution.
2. Role verification (`require_roles(...)`).
3. Resource ownership check (preventing Insecure Direct Object References / IDOR).

### 2.3. Concurrency & Data Integrity Guards
- **PostgreSQL Row-Level Locking (`SELECT ... FOR UPDATE`)**: Eliminates race conditions during slot booking.
- **PostgreSQL Exclusion Constraints (`btree_gist`)**: Database-level mathematical impossibility of overlapping active appointments.

### 2.4. Sanitization, Injection & Transport Security
- **SQL Injection Prevention**: 100% parameterized queries via SQLAlchemy 2.0 ORM and type-checked statements.
- **XSS & Content Security**: Strict Pydantic input schemas and sanitized JSON payloads.
- **CORS Policy**: Restrictive allowed origins specified via environment variables (`CORS_ORIGINS`).
- **Secret Isolation**: Zero credentials in Git or frontend bundles. AI API keys, Google OAuth secrets, and database credentials remain strictly within backend server environments.
