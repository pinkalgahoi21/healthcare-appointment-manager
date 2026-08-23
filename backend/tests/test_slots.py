import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from app.models.doctor_leave import DoctorLeave, LeaveStatus


@pytest.mark.asyncio
async def test_slot_generation_on_working_day(async_client: AsyncClient, admin_auth):
    headers = admin_auth["headers"]
    # 1. Create doctor with 30-min slots
    doc_payload = {
        "name": "Dr. Slot Tester",
        "email": "slot.test@example.com",
        "password": "Password123!",
        "specialization": "General Medicine",
        "slot_duration_minutes": 30,
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=headers)
    assert create_res.status_code == 201
    doc_id = create_res.json()["id"]

    # 2. Pick a future Monday (day_of_week = 0)
    today = date.today()
    days_ahead = (0 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    target_monday = today + timedelta(days=days_ahead)

    # 3. Configure working shift: Monday 09:00 - 11:00 (should yield exactly 4 30-min slots)
    shift_payload = {
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "11:00:00", "is_active": True}
        ]
    }
    wh_res = await async_client.post(
        f"/api/v1/admin/doctors/{doc_id}/working-hours",
        json=shift_payload,
        headers=headers,
    )
    assert wh_res.status_code == 200

    # 4. Query availability
    avail_res = await async_client.get(f"/api/v1/doctors/{doc_id}/slots?date={target_monday.isoformat()}")
    assert avail_res.status_code == 200
    avail_data = avail_res.json()
    assert avail_data["is_on_leave"] is False
    assert len(avail_data["slots"]) == 4
    assert avail_data["slots"][0]["status"] == "available"


@pytest.mark.asyncio
async def test_slot_generation_on_non_working_day(async_client: AsyncClient, admin_auth):
    headers = admin_auth["headers"]
    doc_payload = {
        "name": "Dr. Weekend Off",
        "email": "weekend.off@example.com",
        "password": "Password123!",
        "specialization": "Pediatrics",
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=headers)
    doc_id = create_res.json()["id"]

    # Only works on Monday (day 0)
    await async_client.post(
        f"/api/v1/admin/doctors/{doc_id}/working-hours",
        json={"working_hours": [{"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_active": True}]},
        headers=headers,
    )

    # Query a Sunday (day 6)
    today = date.today()
    days_ahead = (6 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    target_sunday = today + timedelta(days=days_ahead)

    res = await async_client.get(f"/api/v1/doctors/{doc_id}/slots?date={target_sunday.isoformat()}")
    assert res.status_code == 200
    assert len(res.json()["slots"]) == 0


@pytest.mark.asyncio
async def test_slot_generation_idempotency(async_client: AsyncClient, admin_auth):
    headers = admin_auth["headers"]
    doc_payload = {
        "name": "Dr. Idempotent",
        "email": "idem.doc@example.com",
        "password": "Password123!",
        "specialization": "Cardiology",
        "slot_duration_minutes": 60,
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=headers)
    doc_id = create_res.json()["id"]

    today = date.today()
    days_ahead = (2 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    target_wednesday = today + timedelta(days=days_ahead)

    # Wednesday 09:00 - 12:00 -> 3 slots
    await async_client.post(
        f"/api/v1/admin/doctors/{doc_id}/working-hours",
        json={"working_hours": [{"day_of_week": 2, "start_time": "09:00:00", "end_time": "12:00:00", "is_active": True}]},
        headers=headers,
    )

    # Query 1
    res1 = await async_client.get(f"/api/v1/doctors/{doc_id}/slots?date={target_wednesday.isoformat()}")
    assert res1.status_code == 200
    slots1 = res1.json()["slots"]
    assert len(slots1) == 3

    # Query 2 (should return the exact same 3 slots, no duplicate insertion errors)
    res2 = await async_client.get(f"/api/v1/doctors/{doc_id}/slots?date={target_wednesday.isoformat()}")
    assert res2.status_code == 200
    slots2 = res2.json()["slots"]
    assert len(slots2) == 3
    assert [s["id"] for s in slots1] == [s["id"] for s in slots2]


@pytest.mark.asyncio
async def test_doctor_on_leave_slots(async_client: AsyncClient, admin_auth, db_session):
    headers = admin_auth["headers"]
    doc_payload = {
        "name": "Dr. On Leave",
        "email": "leave.doc@example.com",
        "password": "Password123!",
        "specialization": "Dermatology",
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=headers)
    doc_id = create_res.json()["id"]

    today = date.today()
    target_date = today + timedelta(days=10)

    # Insert an approved leave for that date directly
    from uuid import UUID
    leave = DoctorLeave(
        doctor_id=UUID(doc_id),
        leave_date=target_date,
        end_date=target_date,
        reason="Medical Conference",
        status=LeaveStatus.APPROVED.value,
    )
    db_session.add(leave)
    await db_session.commit()

    # Query availability on that date
    res = await async_client.get(f"/api/v1/doctors/{doc_id}/slots?date={target_date.isoformat()}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_on_leave"] is True
    assert data["leave_reason"] == "Medical Conference"
