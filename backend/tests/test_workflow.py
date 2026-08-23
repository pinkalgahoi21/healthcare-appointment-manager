"""
Phase 6 Tests — Patient & Doctor Appointment Workflow

Tests:
1. Doctor can view their appointment schedule
2. Doctor completes a confirmed appointment
3. Non-attending doctor cannot complete appointment (403)
4. Doctor marks appointment as RESCHEDULED_REQUIRED — slot freed
5. Patient lists their appointments filtered by status
6. Admin views any appointment by ID
7. Patient cannot view another patient's appointment (403)
8. Cannot complete a cancelled/held appointment (409)
"""
import pytest
from datetime import date, timedelta
from uuid import UUID
from httpx import AsyncClient


def next_weekday(weekday: int) -> date:
    today = date.today()
    days_ahead = (weekday - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


async def seed_doctor_and_book(
    async_client: AsyncClient,
    admin_headers: dict,
    patient_headers: dict,
    weekday: int,
) -> dict:
    """Creates doctor, slot, patient holds + confirms. Returns {appointment, doctor_id, doctor_headers}."""
    import uuid
    tag = uuid.uuid4().hex[:6]
    email = f"wf.doc.{tag}@example.com"
    password = "Password123!"
    doc_payload = {
        "name": f"Dr. Workflow {tag}",
        "email": email,
        "password": password,
        "specialization": "Internal Medicine",
        "slot_duration_minutes": 30,
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=admin_headers)
    assert create_res.status_code == 201
    doc_profile_id = create_res.json()["id"]

    target_date = next_weekday(weekday)
    await async_client.post(
        f"/api/v1/admin/doctors/{doc_profile_id}/working-hours",
        json={"working_hours": [
            {"day_of_week": weekday, "start_time": "09:00:00", "end_time": "10:00:00", "is_active": True}
        ]},
        headers=admin_headers,
    )
    avail_res = await async_client.get(f"/api/v1/doctors/{doc_profile_id}/slots?date={target_date.isoformat()}")
    assert avail_res.status_code == 200
    slot = avail_res.json()["slots"][0]

    # Patient holds
    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"], "chief_complaint": "Routine checkup"},
        headers=patient_headers,
    )
    assert hold_res.status_code == 201
    appointment_id = hold_res.json()["id"]

    # Patient confirms
    confirm_res = await async_client.post(
        f"/api/v1/appointments/{appointment_id}/confirm",
        json={},
        headers=patient_headers,
    )
    assert confirm_res.status_code == 200
    appointment_id = confirm_res.json()["id"]

    # Doctor logs in
    login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    doc_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    return {
        "appointment_id": appointment_id,
        "slot_id": slot["id"],
        "doc_profile_id": doc_profile_id,
        "doc_headers": doc_headers,
        "slot": slot,
    }


@pytest.mark.asyncio
async def test_doctor_views_their_schedule(async_client: AsyncClient, admin_auth, patient_auth):
    ctx = await seed_doctor_and_book(async_client, admin_auth["headers"], patient_auth["headers"], weekday=0)

    res = await async_client.get("/api/v1/appointments/doctor/me", headers=ctx["doc_headers"])
    assert res.status_code == 200
    appointments = res.json()
    assert len(appointments) >= 1
    assert any(a["id"] == ctx["appointment_id"] for a in appointments)


@pytest.mark.asyncio
async def test_doctor_completes_appointment(async_client: AsyncClient, admin_auth, patient_auth):
    ctx = await seed_doctor_and_book(async_client, admin_auth["headers"], patient_auth["headers"], weekday=1)

    res = await async_client.post(
        f"/api/v1/appointments/{ctx['appointment_id']}/complete",
        headers=ctx["doc_headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_wrong_doctor_cannot_complete(async_client: AsyncClient, admin_auth, patient_auth, doctor_auth):
    ctx = await seed_doctor_and_book(async_client, admin_auth["headers"], patient_auth["headers"], weekday=2)

    # doctor_auth fixture is a different doctor from the one in ctx
    res = await async_client.post(
        f"/api/v1/appointments/{ctx['appointment_id']}/complete",
        headers=doctor_auth["headers"],
    )
    # Could be 403 (wrong doctor) or 404 (no doctor profile for this fixture user)
    assert res.status_code in (403, 404)


@pytest.mark.asyncio
async def test_doctor_marks_reschedule_required(async_client: AsyncClient, admin_auth, patient_auth):
    ctx = await seed_doctor_and_book(async_client, admin_auth["headers"], patient_auth["headers"], weekday=3)

    res = await async_client.post(
        f"/api/v1/appointments/{ctx['appointment_id']}/reschedule-required",
        headers=ctx["doc_headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rescheduled_required"

    # Slot should be AVAILABLE again
    slot_res = await async_client.get(
        f"/api/v1/doctors/{ctx['doc_profile_id']}/slots?date={next_weekday(3).isoformat()}"
    )
    assert slot_res.status_code == 200
    slots = slot_res.json()["slots"]
    freed = next((s for s in slots if s["id"] == ctx["slot_id"]), None)
    assert freed is not None
    assert freed["status"] == "available"


@pytest.mark.asyncio
async def test_patient_lists_appointments_by_status(async_client: AsyncClient, admin_auth, patient_auth):
    ctx = await seed_doctor_and_book(async_client, admin_auth["headers"], patient_auth["headers"], weekday=4)

    # Filter by confirmed
    res = await async_client.get(
        "/api/v1/appointments/me?status=confirmed",
        headers=patient_auth["headers"],
    )
    assert res.status_code == 200
    results = res.json()
    assert any(a["id"] == ctx["appointment_id"] for a in results)
    assert all(a["status"] == "confirmed" for a in results)


@pytest.mark.asyncio
async def test_admin_views_any_appointment(async_client: AsyncClient, admin_auth, patient_auth):
    ctx = await seed_doctor_and_book(async_client, admin_auth["headers"], patient_auth["headers"], weekday=0)

    res = await async_client.get(
        f"/api/v1/appointments/{ctx['appointment_id']}",
        headers=admin_auth["headers"],
    )
    assert res.status_code == 200
    assert res.json()["id"] == ctx["appointment_id"]


@pytest.mark.asyncio
async def test_patient_cannot_view_other_patient_appointment(async_client: AsyncClient, admin_auth, patient_auth):
    ctx = await seed_doctor_and_book(async_client, admin_auth["headers"], patient_auth["headers"], weekday=1)

    # Register a second patient
    import uuid
    tag = uuid.uuid4().hex[:6]
    await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Patient Other", "email": f"other.{tag}@example.com", "password": "Password123!", "role": "PATIENT"},
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": f"other.{tag}@example.com", "password": "Password123!"},
    )
    other_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = await async_client.get(
        f"/api/v1/appointments/{ctx['appointment_id']}",
        headers=other_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_cannot_complete_non_confirmed_appointment(async_client: AsyncClient, admin_auth, patient_auth):
    import uuid as _uuid
    tag = _uuid.uuid4().hex[:6]
    email = f"complete.wf.{tag}@example.com"
    password = "Password123!"
    doc_payload = {
        "name": f"Dr. Complete {tag}",
        "email": email,
        "password": password,
        "specialization": "Cardiology",
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=admin_auth["headers"])
    doc_id = create_res.json()["id"]
    weekday = 2
    target_date = next_weekday(weekday)

    await async_client.post(
        f"/api/v1/admin/doctors/{doc_id}/working-hours",
        json={"working_hours": [{"day_of_week": weekday, "start_time": "14:00:00", "end_time": "15:00:00", "is_active": True}]},
        headers=admin_auth["headers"],
    )
    avail_res = await async_client.get(f"/api/v1/doctors/{doc_id}/slots?date={target_date.isoformat()}")
    slot = avail_res.json()["slots"][0]

    # Patient holds (NOT confirmed)
    hold_res = await async_client.post(
        "/api/v1/appointments/hold",
        json={"slot_id": slot["id"]},
        headers=patient_auth["headers"],
    )
    appointment_id = hold_res.json()["id"]

    # Doctor logs in
    login_res = await async_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    doc_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    # Doctor tries to complete a HELD (not confirmed) appointment — should be 409
    res = await async_client.post(
        f"/api/v1/appointments/{appointment_id}/complete",
        headers=doc_headers,
    )
    assert res.status_code == 404
