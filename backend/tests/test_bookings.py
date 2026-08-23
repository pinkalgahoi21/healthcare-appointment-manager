"""
Phase 5 Tests — Slot Holds & Concurrency-Safe Booking

Tests:
1. Patient can hold an available slot
2. Double-hold attempt returns HTTP 409
3. Patient can confirm within hold window
4. Doctor cannot hold a slot (role restriction)
5. Patient can cancel a held appointment (slot restored to AVAILABLE)
6. Patient can cancel a confirmed appointment
7. Admin can cancel any appointment
8. Expired hold is automatically released on next hold attempt
"""
import asyncio
import pytest
from datetime import date, timedelta, datetime, timezone
from uuid import UUID
from httpx import AsyncClient
from app.models.appointment_slot import AppointmentSlot, SlotStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def seed_doctor_with_slot(async_client: AsyncClient, admin_headers: dict, target_date: date):
    """Creates doctor, assigns working hours, returns (doctor_id, slot)."""
    import uuid
    tag = uuid.uuid4().hex[:6]
    doc_payload = {
        "name": f"Dr. Booking {tag}",
        "email": f"booking.doc.{tag}@example.com",
        "password": "Password123!",
        "specialization": "General Medicine",
        "slot_duration_minutes": 30,
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=admin_headers)
    assert create_res.status_code == 201
    doc_id = create_res.json()["id"]

    day_of_week = target_date.weekday()
    await async_client.post(
        f"/api/v1/admin/doctors/{doc_id}/working-hours",
        json={"working_hours": [
            {"day_of_week": day_of_week, "start_time": "09:00:00", "end_time": "10:00:00", "is_active": True}
        ]},
        headers=admin_headers,
    )

    # Generate slots by querying availability
    avail_res = await async_client.get(f"/api/v1/doctors/{doc_id}/slots?date={target_date.isoformat()}")
    assert avail_res.status_code == 200
    slots = avail_res.json()["slots"]
    assert len(slots) > 0, "No slots generated — check that target_date is a working day"
    return doc_id, slots[0]


def next_weekday(weekday: int) -> date:
    """Return the next occurrence of given weekday (0=Mon .. 6=Sun) after today."""
    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patient_can_hold_slot(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(1)  # Tuesday
    _, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"], "chief_complaint": "Persistent cough"},
        headers=patient_auth["headers"],
    )
    assert hold_res.status_code == 201
    data = hold_res.json()
    assert data["slot_id"] == slot["id"]
    assert data["status"] == "active"
    assert data["patient_id"] == str(patient_auth["user"].id)


@pytest.mark.asyncio
async def test_double_hold_returns_409(async_client: AsyncClient, admin_auth, patient_auth, doctor_auth):
    target_date = next_weekday(2)  # Wednesday
    _, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    # First hold by patient
    r1 = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=patient_auth["headers"],
    )
    assert r1.status_code == 201

    # Second hold attempt on same slot by another patient (register one)
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={
            "name": "Patient Two",
            "email": "patient.two@example.com",
            "password": "Password123!",
            "role": "PATIENT",
        },
    )
    assert reg_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "patient.two@example.com", "password": "Password123!"},
    )
    p2_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    r2 = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=p2_headers,
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_patient_confirms_appointment(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(3)  # Thursday
    _, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    # Hold
    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=patient_auth["headers"],
    )
    assert hold_res.status_code == 201
    appointment_id = hold_res.json()["id"]

    # Confirm
    confirm_res = await async_client.post(
        f"/api/v1/appointments/{appointment_id}/confirm",
        json={},
        headers=patient_auth["headers"],
    )
    assert confirm_res.status_code == 200
    data = confirm_res.json()
    assert data["status"] == "confirmed"
    assert data["confirmed_at"] is not None


@pytest.mark.asyncio
async def test_doctor_cannot_hold_slot(async_client: AsyncClient, admin_auth, doctor_auth):
    target_date = next_weekday(4)  # Friday
    _, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=doctor_auth["headers"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_patient_releases_held_slot(async_client: AsyncClient, admin_auth, patient_auth, db_session):
    target_date = next_weekday(0)  # Monday
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    # Hold
    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=patient_auth["headers"],
    )
    hold_id = hold_res.json()["id"]

    # Cancel
    cancel_res = await async_client.post(
        f"/api/v1/appointments/holds/{hold_id}/release",
        headers=patient_auth["headers"],
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "released"

    # Slot should be available again
    avail_res = await async_client.get(f"/api/v1/doctors/{doc_id}/slots?date={target_date.isoformat()}")
    released_slots = [s for s in avail_res.json()["slots"] if s["id"] == slot["id"]]
    assert released_slots[0]["status"] == "available"


@pytest.mark.asyncio
async def test_patient_cancels_confirmed_appointment(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(1)  # Tuesday
    _, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=patient_auth["headers"],
    )
    appointment_id = hold_res.json()["id"]

    # Confirm
    confirm_res = await async_client.post(
        f"/api/v1/appointments/{appointment_id}/confirm",
        json={},
        headers=patient_auth["headers"],
    )
    assert confirm_res.status_code == 200
    appointment_id = confirm_res.json()["id"]

    # Cancel confirmed
    cancel_res = await async_client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"reason": "Doctor unavailable"},
        headers=patient_auth["headers"],
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_admin_can_cancel_any_appointment(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(2)  # Wednesday
    _, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=patient_auth["headers"],
    )
    appointment_id = hold_res.json()["id"]

    confirm_res = await async_client.post(
        f"/api/v1/appointments/{appointment_id}/confirm",
        json={},
        headers=patient_auth["headers"],
    )
    assert confirm_res.status_code == 200
    appointment_id = confirm_res.json()["id"]

    # Admin cancels a confirmed appointment.
    cancel_res = await async_client.post(
        f"/api/v1/appointments/{appointment_id}/cancel",
        json={"reason": "Admin override"},
        headers=admin_auth["headers"],
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
    assert cancel_res.json()["cancellation_reason"] == "Admin override"


@pytest.mark.asyncio
async def test_cancelled_slot_can_be_booked_again(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(4)
    _, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    first_hold = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=patient_auth["headers"])
    first_confirmation = await async_client.post(
        f"/api/v1/appointments/{first_hold.json()['id']}/confirm", json={}, headers=patient_auth["headers"]
    )
    first_appointment_id = first_confirmation.json()["id"]
    cancellation = await async_client.post(
        f"/api/v1/appointments/{first_appointment_id}/cancel", json={"reason": "Plans changed"}, headers=patient_auth["headers"]
    )
    assert cancellation.status_code == 200

    tag = __import__("uuid").uuid4().hex[:6]
    registration = await async_client.post("/api/v1/auth/register", json={
        "name": "Replacement Patient", "email": f"replacement.{tag}@example.com", "password": "Password123!"
    })
    assert registration.status_code == 201
    second_headers = {"Authorization": f"Bearer {registration.json()['access_token']}"}
    second_hold = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=second_headers)
    assert second_hold.status_code == 201
    second_confirmation = await async_client.post(
        f"/api/v1/appointments/{second_hold.json()['id']}/confirm", json={}, headers=second_headers
    )
    assert second_confirmation.status_code == 200


@pytest.mark.asyncio
async def test_expired_hold_auto_released(async_client: AsyncClient, admin_auth, patient_auth, db_session):
    """
    Simulates hold expiry by directly backdating held_until on the slot,
    then verifies a second patient can acquire the hold.
    """
    from app.models.slot_hold import SlotHold
    from sqlalchemy import select as sa_select

    target_date = next_weekday(3)  # Thursday
    _, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)
    slot_id = slot["id"]

    # Patient 1 holds the slot
    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot_id},
        headers=patient_auth["headers"],
    )
    assert hold_res.status_code == 201

    # Manually expire the hold in the DB
    past = datetime(2000, 1, 1, tzinfo=timezone.utc)
    slot_row_stmt = sa_select(SlotHold).where(SlotHold.id == UUID(hold_res.json()["id"]))
    slot_row_res = await db_session.execute(slot_row_stmt)
    slot_row = slot_row_res.scalar_one()
    slot_row.expires_at = past
    await db_session.commit()

    # Register second patient
    import uuid as _uuid
    tag = _uuid.uuid4().hex[:6]
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Patient Exp", "email": f"exp.{tag}@example.com", "password": "Password123!", "role": "PATIENT"},
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": f"exp.{tag}@example.com", "password": "Password123!"},
    )
    p2_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Second patient should now be able to hold (stale hold auto-released)
    r2 = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot_id},
        headers=p2_headers,
    )
    assert r2.status_code == 201
    assert r2.json()["status"] == "active"
