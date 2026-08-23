from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import health, auth, doctors, admin, appointments, clinical, engagement, integrations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("healthcare_manager")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle
    logger.info("==================================================")
    logger.info(f" Starting {settings.PROJECT_NAME}")
    logger.info(f" Environment: {settings.ENVIRONMENT} (Debug: {settings.DEBUG})")
    logger.info(f" API Docs: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("==================================================")
    yield
    # Shutdown lifecycle
    logger.info("Shutting down application resources...")


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="Production-ready full-stack healthcare appointment and clinical follow-up coordination API.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health checks
    application.include_router(health.router, prefix="/api")
    application.include_router(health.router)

    # Authentication & RBAC
    application.include_router(auth.router, prefix="/api/v1/auth")
    application.include_router(auth.router, prefix="/api/auth")

    # Doctors & Availability
    application.include_router(doctors.router, prefix="/api/v1/doctors")
    application.include_router(doctors.router, prefix="/api/doctors")

    # Admin Management
    application.include_router(admin.router, prefix="/api/v1/admin")
    application.include_router(admin.router, prefix="/api/admin")

    # Appointments (Holds, Confirms, Cancels)
    application.include_router(appointments.router, prefix="/api/v1/appointments")
    application.include_router(appointments.router, prefix="/api/appointments")

    application.include_router(clinical.router, prefix="/api/v1/clinical")
    application.include_router(clinical.router, prefix="/api/clinical")
    application.include_router(engagement.router, prefix="/api/v1/engagement")
    application.include_router(engagement.router, prefix="/api/engagement")

    # Google Calendar OAuth Integration
    application.include_router(integrations.router, prefix="/api/v1/integrations/google")
    application.include_router(integrations.router, prefix="/api/integrations/google")

    @application.get("/", tags=["Root"])
    async def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API",
            "docs": "/docs",
            "health": "/api/health",
        }

    return application


app = create_application()
