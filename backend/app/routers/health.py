from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import settings
from app.database import check_db_health, check_redis_health

router = APIRouter(tags=["Health & System Diagnostics"])


@router.get("/health")
async def health_check():
    """
    System Health Check endpoint.
    Performs live connectivity checks against PostgreSQL and Redis.
    """
    db_health = await check_db_health()
    redis_health = await check_redis_health()

    is_healthy = db_health.get("status") == "connected" and redis_health.get("status") == "connected"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": db_health,
            "redis": redis_health,
        },
    }


@router.get("/health/db")
async def database_health():
    """
    Direct database connectivity health check.
    """
    db_health = await check_db_health()
    return {
        "service": "database",
        "engine": "PostgreSQL 16 (asyncpg)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **db_health,
    }


@router.get("/health/redis")
async def redis_health():
    """
    Direct Redis connectivity health check.
    """
    redis_health = await check_redis_health()
    return {
        "service": "redis",
        "engine": "Redis 7 (aioredis)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **redis_health,
    }
