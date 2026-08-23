from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.appointment import (
    HoldSlotRequest,
    ConfirmAppointmentRequest,
    CancelAppointmentRequest,
    AppointmentResponse,
    SlotHoldResponse,
)
from app.services.booking_service import BookingService
from app.services.doctor_service import DoctorService
from app.auth.dependencies import get_current_user, require_roles

router = APIRouter(tags=["Appointments"])


@router.post("/hold", response_model=SlotHoldResponse, status_code=status.HTTP_201_CREATED)
async def hold_slot(
    payload: HoldSlotRequest,
    current_user: User = Depends(require_roles(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db),
):
    """
    Patient places an auditable, time-limited hold on an available appointment slot.
    Hold window is configured by SLOT_HOLD_DURATION_MINUTES (default: 10 min).
    Returns HTTP 409 if the slot is already held or booked.
    """
    return await BookingService.hold_slot(
        db=db,
        slot_id=payload.slot_id,
        user_id=current_user.id,
        chief_complaint=payload.chief_complaint,
    )


@router.post("/{appointment_id}/confirm", response_model=AppointmentResponse)
async def confirm_appointment(
    appointment_id: UUID,
    payload: ConfirmAppointmentRequest,
    current_user: User = Depends(require_roles(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db),
):
    """
    Patient confirms their held appointment within the hold window.
    Upgrades slot from HELD → BOOKED and appointment from HELD → CONFIRMED.
    Returns HTTP 409 if hold has expired.
    """
    return await BookingService.confirm_appointment(
        db=db,
        appointment_id=appointment_id,
        user_id=current_user.id,
        chief_complaint=payload.chief_complaint,
    )


@router.post("/holds/{hold_id}/release", response_model=SlotHoldResponse)
async def release_hold(
    hold_id: UUID,
    current_user: User = Depends(require_roles(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db),
):
    """Release an active hold without creating or deleting appointment history."""
    return await BookingService.release_hold(db, hold_id, current_user.id)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment(
    appointment_id: UUID,
    payload: CancelAppointmentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a HELD or CONFIRMED appointment.
    - Patients can cancel their own appointments.
    - Doctors and Admins can cancel any appointment.
    Releases the slot back to AVAILABLE.
    """
    return await BookingService.cancel_appointment(
        db=db,
        appointment_id=appointment_id,
        user_id=current_user.id,
        user_role=current_user.role if isinstance(current_user.role, str) else current_user.role.value,
        reason=payload.reason,
    )


@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(
    appointment_id: UUID,
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Doctor marks a CONFIRMED appointment as COMPLETED.
    Only the attending doctor may call this endpoint.
    """
    doctor = await DoctorService.get_by_user_id(db, current_user.id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for current user.",
        )
    return await BookingService.complete_appointment(
        db=db,
        appointment_id=appointment_id,
        doctor_id=doctor.id,
    )


@router.post("/{appointment_id}/reschedule-required", response_model=AppointmentResponse)
async def mark_reschedule_required(
    appointment_id: UUID,
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Doctor flags an appointment as RESCHEDULED_REQUIRED, releasing the slot.
    The patient must rebook.
    """
    doctor = await DoctorService.get_by_user_id(db, current_user.id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found for current user.",
        )
    return await BookingService.mark_reschedule_required(
        db=db,
        appointment_id=appointment_id,
        doctor_id=doctor.id,
    )


@router.get("/me", response_model=List[AppointmentResponse])
async def list_my_appointments(
    appt_status: Optional[str] = Query(None, alias="status", description="Filter by appointment status"),
    current_user: User = Depends(require_roles(UserRole.PATIENT)),
    db: AsyncSession = Depends(get_db),
):
    """
    Patient retrieves their appointment history filtered by optional status.
    """
    return await BookingService.list_patient_appointments(
        db=db,
        patient_id=current_user.id,
        appointment_status=appt_status,
    )


@router.get("/doctor/me", response_model=List[AppointmentResponse])
async def list_doctor_appointments(
    appt_status: Optional[str] = Query(None, alias="status", description="Filter by appointment status"),
    current_user: User = Depends(require_roles(UserRole.DOCTOR)),
    db: AsyncSession = Depends(get_db),
):
    """
    Doctor retrieves their appointment schedule filtered by optional status.
    """
    doctor = await DoctorService.get_by_user_id(db, current_user.id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found.",
        )
    return await BookingService.list_doctor_appointments(
        db=db,
        doctor_id=doctor.id,
        appointment_status=appt_status,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a single appointment by ID.
    Patients and doctors can only access appointments that belong to them;
    administrators can access any appointment.
    """
    appointment = await BookingService.get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appointment '{appointment_id}' not found.",
        )

    user_role = current_user.role if isinstance(current_user.role, str) else current_user.role.value
    if user_role == "PATIENT" and appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )
    if user_role == "DOCTOR":
        doctor = await DoctorService.get_by_user_id(db, current_user.id)
        if not doctor or appointment.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

    return appointment
