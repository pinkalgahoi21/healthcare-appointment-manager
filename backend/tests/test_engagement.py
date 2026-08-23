import pytest
from httpx import AsyncClient
from app.models.user import UserRole
from tests.test_bookings import seed_doctor_with_slot, next_weekday
from app.auth.security import create_access_token


@pytest.mark.asyncio
async def test_patient_pre_visit_summary(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(1)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=patient_auth["headers"])
    confirm_res = await async_client.post(f"/api/v1/appointments/{hold_res.json()['id']}/confirm", json={}, headers=patient_auth["headers"])
    appointment_id = confirm_res.json()["id"]

    summary_res = await async_client.post(
        f"/api/v1/engagement/appointments/{appointment_id}/pre-visit-summary",
        json={"symptoms": "I have had a mild headache and low-grade fever for two days."},
        headers=patient_auth["headers"],
    )
    assert summary_res.status_code == 200
    data = summary_res.json()
    assert "urgency" in data
    assert data["urgency"] in ["LOW", "MEDIUM", "HIGH"]
    assert "suggested_questions" in data
    assert len(data["suggested_questions"]) == 3
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_doctor_post_visit_summary_and_publish_gate(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(2)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=patient_auth["headers"])
    confirm_res = await async_client.post(f"/api/v1/appointments/{hold_res.json()['id']}/confirm", json={}, headers=patient_auth["headers"])
    appointment_id = confirm_res.json()["id"]

    doc_profile_res = await async_client.get(f"/api/v1/doctors/{doc_id}")
    doc_user_id = doc_profile_res.json()["user_id"]
    doc_token = create_access_token(subject=doc_user_id, role="DOCTOR")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # Doctor adds clinical note
    await async_client.put(
        f"/api/v1/clinical/appointments/{appointment_id}/note",
        json={"content": "Acute viral pharyngitis."},
        headers=doc_headers,
    )

    # Doctor generates post-visit summary
    post_res = await async_client.post(
        f"/api/v1/engagement/appointments/{appointment_id}/post-visit-summary",
        json={"follow_up_instructions": "Drink plenty of fluids, rest for 3 days."},
        headers=doc_headers,
    )
    assert post_res.status_code == 200
    summary_data = post_res.json()
    assert summary_data["is_published"] is False
    summary_id = summary_data["id"]

    # Patient tries to read unpublished summary -> should receive 404
    patient_view_res = await async_client.get(
        f"/api/v1/engagement/appointments/{appointment_id}/post-visit-summary",
        headers=patient_auth["headers"],
    )
    assert patient_view_res.status_code == 404

    # Doctor publishes summary
    pub_res = await async_client.post(
        f"/api/v1/engagement/post-visit-summaries/{summary_id}/publish",
        headers=doc_headers,
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["is_published"] is True

    # Patient can now read published summary
    patient_view_res_after = await async_client.get(
        f"/api/v1/engagement/appointments/{appointment_id}/post-visit-summary",
        headers=patient_auth["headers"],
    )
    assert patient_view_res_after.status_code == 200
    assert patient_view_res_after.json()["is_published"] is True


@pytest.mark.asyncio
async def test_patient_medication_reminders_and_notifications(async_client: AsyncClient, admin_auth, patient_auth):
    target_date = next_weekday(3)
    doc_id, slot = await seed_doctor_with_slot(async_client, admin_auth["headers"], target_date)

    hold_res = await async_client.post("/api/v1/appointments/hold", json={"slot_id": slot["id"]}, headers=patient_auth["headers"])
    confirm_res = await async_client.post(f"/api/v1/appointments/{hold_res.json()['id']}/confirm", json={}, headers=patient_auth["headers"])
    appointment_id = confirm_res.json()["id"]

    doc_profile_res = await async_client.get(f"/api/v1/doctors/{doc_id}")
    doc_user_id = doc_profile_res.json()["user_id"]
    doc_token = create_access_token(subject=doc_user_id, role="DOCTOR")
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    rx_res = await async_client.post(
        f"/api/v1/clinical/appointments/{appointment_id}/prescriptions",
        json={"medication_name": "Ibuprofen 400mg", "dosage": "1 tablet", "frequency": "Every 8 hours"},
        headers=doc_headers,
    )
    rx_id = rx_res.json()["id"]

    # Create reminder
    reminder_res = await async_client.post(
        "/api/v1/engagement/reminders",
        json={
            "prescription_id": rx_id,
            "schedule": {"times": ["08:00", "14:00", "20:00"]},
        },
        headers=patient_auth["headers"],
    )
    assert reminder_res.status_code == 200
    assert reminder_res.json()["patient_id"] == str(patient_auth["user"].id)

    # List reminders
    reminders_list = await async_client.get("/api/v1/engagement/reminders/me", headers=patient_auth["headers"])
    assert reminders_list.status_code == 200
    assert len(reminders_list.json()) >= 1

    # Check notifications endpoint
    notifs_res = await async_client.get("/api/v1/engagement/notifications/me", headers=patient_auth["headers"])
    assert notifs_res.status_code == 200
    assert isinstance(notifs_res.json(), list)
