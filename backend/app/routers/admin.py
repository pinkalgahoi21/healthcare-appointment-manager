from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.doctor import (
    DoctorCreateRequest,
    DoctorUpdateRequest,
    DoctorProfileResponse,
    WorkingHoursSetRequest,
    WorkingHoursResponse,
    DoctorLeaveCreateRequest,
    DoctorLeaveResponse,
)
from app.services.doctor_service import DoctorService
from app.services.leave_service import LeaveService
from app.services.user_service import UserService
from app.auth.dependencies import require_roles

router = APIRouter(tags=["Admin Management"])


@router.post("/leaves", response_model=DoctorLeaveResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor_leave(
    payload: DoctorLeaveCreateRequest,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    if not await DoctorService.get_by_id(db, payload.doctor_id):
        raise HTTPException(status_code=404, detail="Doctor not found.")
    return await LeaveService.create(db, payload.doctor_id, payload.leave_date, payload.end_date, payload.reason)


@router.get("/leaves", response_model=List[DoctorLeaveResponse])
async def list_doctor_leaves(
    doctor_id: Optional[UUID] = Query(None),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await LeaveService.list(db, doctor_id)


@router.delete("/leaves/{leave_id}", response_model=DoctorLeaveResponse)
async def remove_doctor_leave(
    leave_id: UUID,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    return await LeaveService.remove(db, leave_id)


@router.post("/doctors", response_model=DoctorProfileResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_doctor(
    payload: DoctorCreateRequest,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Administrator onboards a new practitioner (creates User account with DOCTOR role and DoctorProfile).
    """
    existing_user = await UserService.get_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists.",
        )

    doctor = await DoctorService.create_doctor(db=db, payload=payload)
    return DoctorService.to_response_dto(doctor)


@router.put("/doctors/{id}", response_model=DoctorProfileResponse)
async def admin_update_doctor(
    id: UUID,
    payload: DoctorUpdateRequest,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Administrator updates doctor specialization, bio, slot duration, or consultation fee.
    """
    doctor = await DoctorService.get_by_id(db, id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{id}' was not found.",
        )

    updated = await DoctorService.update_doctor(db, id, payload)
    return DoctorService.to_response_dto(updated)


@router.post("/doctors/{id}/working-hours", response_model=List[WorkingHoursResponse])
async def admin_set_doctor_working_hours(
    id: UUID,
    payload: WorkingHoursSetRequest,
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Administrator configures working shifts for a doctor.
    """
    doctor = await DoctorService.get_by_id(db, id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID '{id}' was not found.",
        )

    records = await DoctorService.set_working_hours(db, id, payload.working_hours)
    return [WorkingHoursResponse.model_validate(r) for r in records]


@router.get("/doctors", response_model=List[DoctorProfileResponse])
async def admin_list_doctors(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(require_roles(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """
    Administrator lists all doctor profiles.
    """
    doctors = await DoctorService.list_doctors(db=db, limit=limit, offset=offset)
    return [DoctorService.to_response_dto(d) for d in doctors]
