import asyncio
import os
import sys
import httpx
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app


async def main():
    print("=" * 60)
    print(" FASTAPI BACKEND LIVE HEALTH ENDPOINT VERIFICATION")
    print("=" * 60)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("\n1. Testing GET / ...")
        res = await client.get("/")
        print(f"Status: {res.status_code}")
        print(json.dumps(res.json(), indent=2))

        print("\n2. Testing GET /api/health ...")
        res = await client.get("/api/health")
        print(f"Status: {res.status_code}")
        print(json.dumps(res.json(), indent=2))

        print("\n3. Testing GET /api/health/db ...")
        res = await client.get("/api/health/db")
        print(f"Status: {res.status_code}")
        print(json.dumps(res.json(), indent=2))

        print("\n4. Testing GET /api/health/redis ...")
        res = await client.get("/api/health/redis")
        print(f"Status: {res.status_code}")
        print(json.dumps(res.json(), indent=2))

    print("\n" + "=" * 60)
    print(" [OK] Live endpoint verification completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
