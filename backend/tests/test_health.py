import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "health" in data
    assert data["health"] == "/api/health"


@pytest.mark.asyncio
async def test_health_endpoint_structure(async_client: AsyncClient):
    response = await async_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "status" in data["services"]["database"]
    assert "status" in data["services"]["redis"]


@pytest.mark.asyncio
async def test_database_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "database"
    assert "status" in data
    assert "engine" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_redis_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/health/redis")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "redis"
    assert "status" in data
    assert "engine" in data
    assert "timestamp" in data
