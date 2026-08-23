import pytest
from httpx import AsyncClient
from app.models.user import UserRole
from tests.test_bookings import seed_doctor_with_slot, next_weekday
from app.auth.security import create_access_token


@pytest.mark.asyncio
async def test_patient_cannot_access_other_patient_prescriptions(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(1)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    # Patient 1 books
    hold_res = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=patient_auth["headers"])
    confirm_res = await async_client.post(f"/api/v1/appointments/{hold_res.json()['id']}/confirm", json={}, headers=patient_auth["headers"])
    appointment_id = confirm_res.json()["id"]

    doc_profile_res = await async_client.get(f"/api/v1/doctors/{doc_id}")
    doc_user_id = doc_profile_res.json()["user_id"]
    doc_token = create_access_token(subject=doc_user_id, role="DOCTOR")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    rx_res = await async_client.post(
        f"/api/v1/clinical/appointments/{appointment_id}/prescriptions",
        json={"medication_name": "Atorvastatin 20mg", "dosage": "1 tab", "frequency": "Daily at bedtime"},
        headers=doc_headers,
    )
    rx_id = rx_res.json()["id"]

    # Patient 2 registers
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"name": "Patient Snooper", "email": "snooper@example.com", "password": "Password123!", "role": "PATIENT"},
    )
    p2_headers = {"Authorization": f"Bearer {reg_res.json()['access_token']}"}

    # Patient 2 creates reminder on Patient 1's prescription -> must be 403 Forbidden
    hack_res = await async_client.post(
        "/api/v1/engagement/reminders",
        json={"prescription_id": rx_id, "schedule": {"times": ["21:00"]}},
        headers=p2_headers,
    )
    assert hack_res.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_doctor_leave(async_client: AsyncClient, admin_auth, patient_auth, doctor_auth):
    target_date = next_weekday(2)
    doc_id, _ = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    leave_payload = {
        "doctor_id": doc_id,
        "leave_date": target_date.isoformat(),
        "end_date": target_date.isoformat(),
        "reason": "Emergency surgery training",
    }

    # Patient attempts to place doctor on leave -> 403
    p_res = await async_client.post("/api/v1/admin/leaves", json=leave_payload, headers=patient_auth["headers"])
    assert p_res.status_code == 403

    # Doctor attempts to approve leave through admin route -> 403
    d_res = await async_client.post("/api/v1/admin/leaves", json=leave_payload, headers=doctor_auth["headers"])
    assert d_res.status_code == 403

    # Admin succeeds
    a_res = await async_client.post("/api/v1/admin/leaves", json=leave_payload, headers=admin_auth["headers"])
    assert a_res.status_code == 201


@pytest.mark.asyncio
async def test_production_secret_key_validation():
    from app.config import Settings
    import pytest as pt

    with pt.raises(ValueError, match="SECRET_KEY must be a unique value"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="change-this-to-a-super-secret-key-in-production-min-32-chars",
        )
