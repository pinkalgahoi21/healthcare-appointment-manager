from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.doctor import (
    DoctorProfileResponse,
    DoctorUpdateRequest,
    WorkingHoursSetRequest,
    WorkingHoursResponse,
    SpecializationListResponse,
)
from app.schemas.slot import (
    DoctorAvailabilityResponse,
    SlotGenerateRequest,
    SlotResponse,
)
from app.services.doctor_service import DoctorService
from app.services.slot_service import SlotService
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(tags=["Doctors & Availability"])


@router.get("", response_model=List[DoctorProfileResponse])
async def list_doctors(
    specialization: Optional[str] = Query(None, description="Filter by medical specialization"),
    search: Optional[str] = Query(None, description="Search by doctor name or keywords"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Public / Patient doctor discovery directory with search and specialization filter.
    """
    doctors = await DoctorService.list_doctors(
        db=db,
        specialization=specialization,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [DoctorService.to_response_dto(d) for d in doctors]


@router.get("/specializations", response_model=SpecializationListResponse)
async def list_specializations(
    db: AsyncSession = Depends(get_db),
):
    """
    Returns list of all active medical specializations across clinic doctors.
    """
    specs = await DoctorService.list_specializations(db)
    return SpecializationListResponse(specializations=specs)


@router.get("/me", response_model=DoctorProfileResponse)
async def get_my_doctor_profile(
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Doctor retrieves their own practitioner profile and working hours.
    """
    doctor = await DoctorService.get_by_user_id(db, current_user.id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for current user account.",
        )
    return DoctorService.to_response_dto(doctor)


@router.put("/me", response_model=DoctorProfileResponse)
async def update_my_doctor_profile(
    payload: DoctorUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Doctor updates their bio, specialization, slot duration, or consultation fee.
    """
    doctor = await DoctorService.get_by_user_id(db, current_user.id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found.",
        )
    updated = await DoctorService.update_doctor(db, doctor.id, payload)
    return DoctorService.to_response_dto(updated)


@router.post("/me/working-hours", response_model=List[WorkingHoursResponse])
async def set_my_working_hours(
    payload: WorkingHoursSetRequest,
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Doctor configures their weekly shift schedule.
    """
    doctor = await DoctorService.get_by_user_id(db, current_user.id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found.",
        )
    records = await DoctorService.set_working_hours(db, doctor.id, payload.working_hours)
    return [WorkingHoursResponse.model_validate(r) for r in records]


@router.get("/{id}", response_model=DoctorProfileResponse)
async def get_doctor_by_id(
    id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve full doctor profile by Doctor ID.
    """
    doctor = await DoctorService.get_by_id(db, id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{id}' was not found.",
        )
    return DoctorService.to_response_dto(doctor)


@router.get("/{id}/working-hours", response_model=List[WorkingHoursResponse])
async def get_doctor_working_hours(
    id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve doctor's weekly working hours by Doctor ID.
    """
    doctor = await DoctorService.get_by_id(db, id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{id}' was not found.",
        )
    records = await DoctorService.get_working_hours(db, id)
    return [WorkingHoursResponse.model_validate(r) for r in records]


@router.get("/{id}/slots", response_model=DoctorAvailabilityResponse)
async def get_doctor_slots(
    id: UUID,
    date_param: date = Query(..., alias="date", description="Target calendar date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get available appointment slots for a doctor on a specific date.
    Automatically generates persisted slots based on working hours if not already created.
    """
    doctor = await DoctorService.get_by_id(db, id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{id}' was not found.",
        )
    availability = await SlotService.get_availability(db, id, date_param)
    return availability


@router.post("/{id}/slots/generate", response_model=DoctorAvailabilityResponse)
async def generate_doctor_slots(
    id: UUID,
    payload: SlotGenerateRequest,
    current_admin: User = Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Explicitly triggers slot generation for a doctor on a given date.
    """
    doctor = await DoctorService.get_by_id(db, id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{id}' was not found.",
        )
    availability = await SlotService.get_availability(db, id, payload.start_date)
    return availability
