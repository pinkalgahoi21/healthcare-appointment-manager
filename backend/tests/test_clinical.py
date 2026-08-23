import pytest
from httpx import AsyncClient
from app.models.user import UserRole
from tests.test_bookings import seed_doctor_with_slot, next_weekday


@pytest.mark.asyncio
async def test_doctor_can_upsert_clinical_note(async_client: AsyncClient, admin_auth, patient_auth, doctor_auth):
    target_date = next_weekday(1)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    # Patient holds & confirms
    hold_res = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=patient_auth["headers"])
    assert hold_res.status_code == 201
    confirm_res = await async_client.post(f"/api/v1/appointments/{hold_res.json()['id']}/confirm", json={}, headers=patient_auth["headers"])
    assert confirm_res.status_code == 200
    appointment_id = confirm_res.json()["id"]

    # We need the token for the doctor who owns this appointment
    # Log in as the doctor created in seed_doctor_with_slot
    # In seed_doctor_with_slot, email is booking.doc.<tag>@example.com, password Password123!
    # Let's get the doctor's user
    doc_profile_res = await async_client.get(f"/api/v1/doctors/{doc_id}")
    doc_user_id = doc_profile_res.json()["user_id"]
    from app.auth.security import create_access_token
    doc_token = create_access_token(subject=doc_user_id, role="DOCTOR")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # Doctor upserts clinical note
    note_res = await async_client.put(
        f"/api/v1/clinical/appointments/{appointment_id}/note",
        json={"content": "Patient presents with mild respiratory congestion. Vitals stable."},
        headers=doc_headers,
    )
    assert note_res.status_code == 200
    assert note_res.json()["content"] == "Patient presents with mild respiratory congestion. Vitals stable."

    # Update the note
    update_res = await async_client.put(
        f"/api/v1/clinical/appointments/{appointment_id}/note",
        json={"content": "Updated: Patient prescribed inhaler, follow-up in 7 days."},
        headers=doc_headers,
    )
    assert update_res.status_code == 200
    assert "Updated: Patient prescribed inhaler" in update_res.json()["content"]


@pytest.mark.asyncio
async def test_doctor_creates_prescription_and_patient_reads(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(2)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=patient_auth["headers"])
    confirm_res = await async_client.post(f"/api/v1/appointments/{hold_res.json()['id']}/confirm", json={}, headers=patient_auth["headers"])
    appointment_id = confirm_res.json()["id"]

    doc_profile_res = await async_client.get(f"/api/v1/doctors/{doc_id}")
    doc_user_id = doc_profile_res.json()["user_id"]
    from app.auth.security import create_access_token
    doc_token = create_access_token(subject=doc_user_id, role="DOCTOR")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    rx_payload = {
        "medication_name": "Amoxicillin 500mg",
        "dosage": "1 capsule",
        "frequency": "Three times daily with meals",
        "instructions": "Complete entire 7-day course",
    }
    rx_res = await async_client.post(
        f"/api/v1/clinical/appointments/{appointment_id}/prescriptions",
        json=rx_payload,
        headers=doc_headers,
    )
    assert rx_res.status_code == 201
    rx_data = rx_res.json()
    assert rx_data["medication_name"] == "Amoxicillin 500mg"
    assert rx_data["patient_id"] == str(patient_auth["user"].id)

    # Patient lists prescriptions
    my_rx_res = await async_client.get("/api/v1/clinical/prescriptions/me", headers=patient_auth["headers"])
    assert my_rx_res.status_code == 200
    prescriptions = my_rx_res.json()
    assert any(p["medication_name"] == "Amoxicillin 500mg" for p in prescriptions)


@pytest.mark.asyncio
async def test_wrong_doctor_cannot_add_clinical_notes(async_client: AsyncClient, admin_auth, patient_auth, doctor_auth):
    target_date = next_weekday(3)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=patient_auth["headers"])
    confirm_res = await async_client.post(f"/api/v1/appointments/{hold_res.json()['id']}/confirm", json={}, headers=patient_auth["headers"])
    appointment_id = confirm_res.json()["id"]

    # Use a different doctor's auth header
    diff_doc_headers = doctor_auth["headers"]

    # Attempt to write note for an appointment assigned to doctor 1
    note_res = await async_client.put(
        f"/api/v1/clinical/appointments/{appointment_id}/note",
        json={"content": "Unauthorized note attempt"},
        headers=diff_doc_headers,
    )
    assert note_res.status_code == 404 or note_res.status_code == 403
