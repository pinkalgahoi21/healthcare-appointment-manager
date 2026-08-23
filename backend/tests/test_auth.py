import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_patient_registration_success(async_client: AsyncClient):
    payload = {
        "name": "Sarah Connor",
        "email": "sarah.connor@example.com",
        "password": "Password123!",
        "phone": "+1555123456",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "sarah.connor@example.com"
    assert data["user"]["name"] == "Sarah Connor"
    assert data["user"]["role"] == "PATIENT"
    assert data["user"]["is_active"] is True
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]


@pytest.mark.asyncio
async def test_registration_duplicate_email(async_client: AsyncClient):
    payload = {
        "name": "John Doe",
        "email": "duplicate@example.com",
        "password": "Password123!",
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt second registration with same email
    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_registration_validation_errors(async_client: AsyncClient):
    # Invalid email and short password
    payload = {
        "name": "J",
        "email": "not-an-email",
        "password": "123",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    # First register
    register_payload = {
        "name": "Login User",
        "email": "login.user@example.com",
        "password": "MySecretPassword123!",
    }
    reg_res = await async_client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201

    # Login
    login_payload = {
        "email": "login.user@example.com",
        "password": "MySecretPassword123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login.user@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    login_payload = {
        "email": "login.user@example.com",
        "password": "WrongPassword!",
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    login_payload = {
        "email": "does.not.exist@example.com",
        "password": "Password123!",
    }
    response = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_success(async_client: AsyncClient, patient_auth):
    headers = patient_auth["headers"]
    response = await async_client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == patient_auth["user"].email
    assert data["role"] == "PATIENT"


@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client: AsyncClient):
    # No header
    response = await async_client.get("/api/v1/auth/me")
    assert response.status_code == 401

    # Malformed / invalid token
    response_bad = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert response_bad.status_code == 401


@pytest.mark.asyncio
async def test_role_based_access_control(
    async_client: AsyncClient,
    patient_auth,
    doctor_auth,
    admin_auth,
):
    # Patient role checks
    p_headers = patient_auth["headers"]
    res_p_on_p = await async_client.get("/api/v1/auth/patient-only", headers=p_headers)
    assert res_p_on_p.status_code == 200

    res_p_on_d = await async_client.get("/api/v1/auth/doctor-only", headers=p_headers)
    assert res_p_on_d.status_code == 403

    res_p_on_a = await async_client.get("/api/v1/auth/admin-only", headers=p_headers)
    assert res_p_on_a.status_code == 403

    # Doctor role checks
    d_headers = doctor_auth["headers"]
    res_d_on_d = await async_client.get("/api/v1/auth/doctor-only", headers=d_headers)
    assert res_d_on_d.status_code == 200

    res_d_on_a = await async_client.get("/api/v1/auth/admin-only", headers=d_headers)
    assert res_d_on_a.status_code == 403

    # Admin role checks
    a_headers = admin_auth["headers"]
    res_a_on_a = await async_client.get("/api/v1/auth/admin-only", headers=a_headers)
    assert res_a_on_a.status_code == 200
