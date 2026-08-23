import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_creates_doctor(async_client: AsyncClient, admin_auth):
    headers = admin_auth["headers"]
    payload = {
        "name": "Dr. Gregory House",
        "email": "house.md@example.com",
        "password": "DiagnosisPassword123!",
        "specialization": "Nephrology",
        "bio": "Specialist in diagnostic medicine and nephrology.",
        "slot_duration_minutes": 45,
        "consultation_fee": 150.00,
        "phone": "+1555019283",
    }
    response = await async_client.post("/api/v1/admin/doctors", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dr. Gregory House"
    assert data["email"] == "house.md@example.com"
    assert data["specialization"] == "Nephrology"
    assert data["slot_duration_minutes"] == 45
    assert float(data["consultation_fee"]) == 150.00
    assert "id" in data


@pytest.mark.asyncio
async def test_non_admin_cannot_create_doctor(async_client: AsyncClient, patient_auth):
    headers = patient_auth["headers"]
    payload = {
        "name": "Dr. Hacker",
        "email": "hacker@example.com",
        "password": "Password123!",
        "specialization": "Surgery",
    }
    response = await async_client.post("/api/v1/admin/doctors", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_and_filter_doctors(async_client: AsyncClient, admin_auth):
    headers = admin_auth["headers"]
    # Seed two doctors
    doc1 = {
        "name": "Dr. James Wilson",
        "email": "wilson.onc@example.com",
        "password": "Password123!",
        "specialization": "Oncology",
        "slot_duration_minutes": 30,
    }
    doc2 = {
        "name": "Dr. Lisa Cuddy",
        "email": "cuddy.endo@example.com",
        "password": "Password123!",
        "specialization": "Endocrinology",
        "slot_duration_minutes": 30,
    }
    await async_client.post("/api/v1/admin/doctors", json=doc1, headers=headers)
    await async_client.post("/api/v1/admin/doctors", json=doc2, headers=headers)

    # 1. Public list
    res_all = await async_client.get("/api/v1/doctors")
    assert res_all.status_code == 200
    doctors_all = res_all.json()
    assert len(doctors_all) >= 2

    # 2. Filter by specialization
    res_onc = await async_client.get("/api/v1/doctors?specialization=Oncology")
    assert res_onc.status_code == 200
    docs_onc = res_onc.json()
    assert any(d["specialization"] == "Oncology" for d in docs_onc)
    assert all("Oncology".lower() in d["specialization"].lower() for d in docs_onc)

    # 3. Search by keyword
    res_search = await async_client.get("/api/v1/doctors?search=Cuddy")
    assert res_search.status_code == 200
    docs_search = res_search.json()
    assert any("Cuddy" in d["name"] for d in docs_search)


@pytest.mark.asyncio
async def test_list_specializations(async_client: AsyncClient, admin_auth):
    headers = admin_auth["headers"]
    doc = {
        "name": "Dr. Allison Cameron",
        "email": "cameron.cardio@example.com",
        "password": "Password123!",
        "specialization": "Cardiology",
    }
    await async_client.post("/api/v1/admin/doctors", json=doc, headers=headers)

    res = await async_client.get("/api/v1/doctors/specializations")
    assert res.status_code == 200
    specs = res.json()["specializations"]
    assert "Cardiology" in specs


@pytest.mark.asyncio
async def test_get_doctor_by_id(async_client: AsyncClient, admin_auth):
    headers = admin_auth["headers"]
    doc_payload = {
        "name": "Dr. Robert Chase",
        "email": "chase.ic@example.com",
        "password": "Password123!",
        "specialization": "Intensive Care",
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=headers)
    assert create_res.status_code == 201
    doc_id = create_res.json()["id"]

    get_res = await async_client.get(f"/api/v1/doctors/{doc_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == doc_id
    assert data["name"] == "Dr. Robert Chase"
    assert data["specialization"] == "Intensive Care"


@pytest.mark.asyncio
async def test_doctor_configures_working_hours(async_client: AsyncClient, admin_auth):
    # Admin creates doctor
    headers = admin_auth["headers"]
    doc_payload = {
        "name": "Dr. Eric Foreman",
        "email": "foreman.neuro@example.com",
        "password": "Password123!",
        "specialization": "Neurology",
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=headers)
    assert create_res.status_code == 201
    doc_id = create_res.json()["id"]

    # Doctor logs in
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "foreman.neuro@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    doc_token = login_res.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # Doctor configures working shifts (e.g. Mon, Wed, Fri 09:00 - 17:00)
    shifts = {
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00", "is_active": True},
            {"day_of_week": 2, "start_time": "09:00:00", "end_time": "17:00:00", "is_active": True},
            {"day_of_week": 4, "start_time": "09:00:00", "end_time": "17:00:00", "is_active": True},
        ]
    }
    wh_res = await async_client.post("/api/v1/doctors/me/working-hours", json=shifts, headers=doc_headers)
    assert wh_res.status_code == 200
    wh_data = wh_res.json()
    assert len(wh_data) == 3

    # Public user queries doctor working hours
    pub_wh_res = await async_client.get(f"/api/v1/doctors/{doc_id}/working-hours")
    assert pub_wh_res.status_code == 200
    assert len(pub_wh_res.json()) == 3


@pytest.mark.asyncio
async def test_working_hours_validation_error(async_client: AsyncClient, admin_auth):
    # End time before start time must fail validation
    invalid_shifts = {
        "working_hours": [
            {"day_of_week": 0, "start_time": "17:00:00", "end_time": "09:00:00", "is_active": True}
        ]
    }
    # Login as doctor created in earlier test or admin
    doc_payload = {
        "name": "Dr. Validation",
        "email": "val.doc@example.com",
        "password": "Password123!",
        "specialization": "Pediatrics",
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=admin_auth["headers"])
    assert create_res.status_code == 201

    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "val.doc@example.com", "password": "Password123!"},
    )
    doc_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

    res = await async_client.post("/api/v1/doctors/me/working-hours", json=invalid_shifts, headers=doc_headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_admin_updates_doctor_profile(async_client: AsyncClient, admin_auth):
    headers = admin_auth["headers"]
    doc_payload = {
        "name": "Dr. Update Test",
        "email": "update.doc@example.com",
        "password": "Password123!",
        "specialization": "Dermatology",
        "consultation_fee": 100.00,
    }
    create_res = await async_client.post("/api/v1/admin/doctors", json=doc_payload, headers=headers)
    doc_id = create_res.json()["id"]

    update_payload = {
        "specialization": "Cosmetic Dermatology",
        "consultation_fee": 180.00,
        "slot_duration_minutes": 20,
    }
    update_res = await async_client.put(f"/api/v1/admin/doctors/{doc_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["specialization"] == "Cosmetic Dermatology"
    assert float(data["consultation_fee"]) == 180.00
    assert data["slot_duration_minutes"] == 20
