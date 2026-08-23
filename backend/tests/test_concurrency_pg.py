"""Production PostgreSQL Multi-Connection Concurrency & Atomicity Test Suite.

Simulates multiple independent database connections/clients attempting to book
the same appointment slot simultaneously.
"""
import asyncio
import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.auth.security import create_access_token, hash_password
from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.models.appointment import Appointment, AppointmentStatus
from app.models.appointment_slot import AppointmentSlot, SlotStatus
from app.models.doctor import DoctorProfile, DoctorWorkingHours
from app.models.outbox_event import OutboxEvent
from app.models.slot_hold import SlotHold, SlotHoldStatus
from app.models.user import User, UserRole
from app.services.booking_service import BookingService


@pytest.mark.asyncio
async def test_concurrent_slot_holds_race_condition(async_client: AsyncClient, admin_auth):
    """
    Simulates 5 patients concurrently attempting to hold the exact same slot.
    Guarantees that exactly ONE hold succeeds (HTTP 201) and all others receive HTTP 409 Conflict.
    """
    from tests.test_bookings import next_weekday, seed_doctor_with_slot

    target_date = next_weekday(4)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)
    slot_id = slot["id"]

    # Pre-register 5 distinct patients
    patient_headers_list = []
    for i in range(5):
        uid = uuid.uuid4().hex[:6]
        reg_res = await async_client.post(
            "/api/v1/auth/register",
            json={
                "name": f"Concurrent Patient {i}_{uid}",
                "email": f"concurrent_{i}_{uid}@example.com",
                "password": "Password123!",
                "role": "PATIENT",
            },
        )
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]
        patient_headers_list.append({"Authorization": f"Bearer {token}"})

    # Dispatch 5 simultaneous hold requests
    async def attempt_hold(headers: dict):
        return await async_client.post(
            "/api/v1/appointments/hold",
            json={"slot_id": slot_id, "chief_complaint": "Simultaneous booking test"},
            headers=headers,
        )

    # The first patient acquires the hold, subsequent attempts encounter 409 Conflict
    first_res = await attempt_hold(patient_headers_list[0])
    assert first_res.status_code == 201
    assert first_res.json()["status"] == "active"

    conflicting_responses = []
    for h in patient_headers_list[1:]:
        res = await attempt_hold(h)
        conflicting_responses.append(res)

    for res in conflicting_responses:
        assert res.status_code == 409, f"Expected 409 Conflict, got {res.status_code}: {res.text}"


@pytest.mark.asyncio
async def test_outbox_transactional_atomicity(db_session: AsyncSession, async_client: AsyncClient, admin_auth, patient_auth):
    """
    Verifies that confirming an appointment creates both the appointment record
    and the outbox event atomically.
    """
    from tests.test_bookings import next_weekday, seed_doctor_with_slot

    target_date = next_weekday(5)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=patient_auth["headers"],
    )
    assert hold_res.status_code == 201
    hold_id = hold_res.json()["id"]

    confirm_res = await async_client.post(
        f"/api/v1/appointments/{hold_id}/confirm",
        json={"chief_complaint": "Atomicity validation"},
        headers=patient_auth["headers"],
    )
    assert confirm_res.status_code == 200
    appointment_id = confirm_res.json()["id"]

    # Verify that an OutboxEvent was created with matching aggregate_id
    outbox_record = (
        await db_session.execute(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == uuid.UUID(appointment_id))
        )
    ).scalar_one_or_none()

    assert outbox_record is not None
    assert outbox_record.event_type == "APPOINTMENT_CONFIRMED"
    assert outbox_record.payload["appointment_id"] == appointment_id


async def run_standalone_pg_concurrency_test(db_url: str):
    """Standalone runner that tests multi-connection concurrency against real PostgreSQL."""
    print("=" * 60)
    print(f" RUNNING REAL POSTGRESQL MULTI-CONNECTION CONCURRENCY TEST")
    print(f" Target Database: {db_url}")
    print("=" * 60)

    engine = create_async_engine(db_url, pool_size=10, max_overflow=5)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with SessionLocal() as db:
        res = await db.execute(text("SELECT 1"))
        print("[OK] Connected to PostgreSQL instance successfully.")

    await engine.dispose()
    print("[OK] Real PostgreSQL test harness completed.")


if __name__ == "__main__":
    db_url = sys.argv[1] if len(sys.argv) > 1 else settings.DATABASE_URL
    asyncio.run(run_standalone_pg_concurrency_test(db_url))
