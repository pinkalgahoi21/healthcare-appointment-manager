"""Google Calendar OAuth 2.0 integration endpoints for doctors."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile
from app.models.calendar import DoctorCalendarCredential, GoogleCalendarSync, CalendarSyncStatus
from app.services.calendar_service import GoogleCalendarService

router = APIRouter(tags=["Google Calendar Integration"])


@router.get("/connect")
async def get_google_calendar_connect_url(
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate Google OAuth 2.0 authorization URL for the authenticated doctor.
    The doctor is redirected to Google's consent screen to grant calendar access.
    """
    doctor = (await db.execute(
        select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
    )).scalar_one_or_none()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No doctor profile found for this user.",
        )

    auth_url = GoogleCalendarService.get_oauth_authorization_url(doctor.id)
    return {
        "authorization_url": auth_url,
        "message": "Redirect the user to this URL to initiate Google Calendar OAuth consent.",
    }


@router.get("/callback")
async def google_calendar_oauth_callback(
    code: str = Query(..., description="Authorization code from Google OAuth redirect"),
    state: str = Query(..., description="Doctor profile ID passed as OAuth state"),
    db: AsyncSession = Depends(get_db),
):
    """
    Google OAuth 2.0 callback handler.
    Exchanges the authorization code for access and refresh tokens,
    then persists credentials for the doctor.
    """
    from uuid import UUID

    try:
        doctor_id = UUID(state)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter. Expected a valid doctor profile UUID.",
        )

    # Verify doctor exists
    doctor = (await db.execute(
        select(DoctorProfile).where(DoctorProfile.id == doctor_id)
    )).scalar_one_or_none()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for the provided state.",
        )

    credential = await GoogleCalendarService.exchange_code_for_tokens(db, doctor_id, code)
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to exchange authorization code for tokens.",
        )

    return {
        "message": "Google Calendar connected successfully.",
        "doctor_id": str(doctor_id),
        "calendar_id": credential.calendar_id,
        "is_connected": credential.is_connected,
    }


@router.get("/status")
async def get_calendar_connection_status(
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Check the current Google Calendar connection status for the authenticated doctor.
    """
    doctor = (await db.execute(
        select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
    )).scalar_one_or_none()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No doctor profile found for this user.",
        )

    credential = (await db.execute(
        select(DoctorCalendarCredential).where(DoctorCalendarCredential.doctor_id == doctor.id)
    )).scalar_one_or_none()

    if not credential:
        return {
            "is_connected": False,
            "calendar_id": None,
            "message": "Google Calendar not connected. Use /connect to start OAuth flow.",
        }

    # Get recent sync records
    syncs = (await db.execute(
        select(GoogleCalendarSync)
        .where(GoogleCalendarSync.doctor_id == doctor.id)
        .order_by(GoogleCalendarSync.last_synced_at.desc())
        .limit(5)
    )).scalars().all()

    return {
        "is_connected": credential.is_connected,
        "calendar_id": credential.calendar_id,
        "last_updated": credential.updated_at.isoformat() if credential.updated_at else None,
        "recent_syncs": [
            {
                "appointment_id": str(s.appointment_id),
                "google_event_id": s.google_event_id,
                "sync_status": s.sync_status,
                "last_synced_at": s.last_synced_at.isoformat() if s.last_synced_at else None,
                "error_message": s.error_message,
            }
            for s in syncs
        ],
    }


@router.delete("/disconnect")
async def disconnect_google_calendar(
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke and remove Google Calendar credentials for the authenticated doctor.
    Existing synced events remain on the calendar but will no longer be updated.
    """
    doctor = (await db.execute(
        select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
    )).scalar_one_or_none()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No doctor profile found for this user.",
        )

    credential = (await db.execute(
        select(DoctorCalendarCredential).where(DoctorCalendarCredential.doctor_id == doctor.id)
    )).scalar_one_or_none()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Google Calendar connection exists for this doctor.",
        )

    credential.is_connected = False
    await db.commit()

    return {
        "message": "Google Calendar disconnected. Events will no longer be synchronized.",
        "doctor_id": str(doctor.id),
    }
