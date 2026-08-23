from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.appointment import Appointment
from app.models.clinical import ClinicalNote, Prescription
from app.models.doctor import DoctorProfile
from app.models.user import User, UserRole
from app.schemas.clinical import ClinicalNoteResponse, ClinicalNoteUpsert, PrescriptionCreate, PrescriptionResponse

router = APIRouter(tags=["Clinical records"])


async def _doctor_for_user(db: AsyncSession, user: User) -> DoctorProfile:
    doctor = (await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))).scalar_one_or_none()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found.")
    return doctor


async def _doctor_appointment(db: AsyncSession, appointment_id: UUID, user: User) -> Appointment:
    doctor = await _doctor_for_user(db, user)
    appointment = (await db.execute(select(Appointment).where(Appointment.id == appointment_id))).scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if appointment.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="This appointment is not assigned to you.")
    return appointment


@router.put("/appointments/{appointment_id}/note", response_model=ClinicalNoteResponse)
async def upsert_note(appointment_id: UUID, payload: ClinicalNoteUpsert, user: User = Depends(require_roles(UserRole.DOCTOR)), db: AsyncSession = Depends(get_db)):
    appointment = await _doctor_appointment(db, appointment_id, user)
    note = (await db.execute(select(ClinicalNote).where(ClinicalNote.appointment_id == appointment.id))).scalar_one_or_none()
    doctor = await _doctor_for_user(db, user)
    if note:
        note.content = payload.content
    else:
        note = ClinicalNote(appointment_id=appointment.id, doctor_id=doctor.id, content=payload.content)
        db.add(note)
    await db.commit(); await db.refresh(note)
    return note


@router.post("/appointments/{appointment_id}/prescriptions", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_prescription(appointment_id: UUID, payload: PrescriptionCreate, user: User = Depends(require_roles(UserRole.DOCTOR)), db: AsyncSession = Depends(get_db)):
    appointment = await _doctor_appointment(db, appointment_id, user)
    doctor = await _doctor_for_user(db, user)
    prescription = Prescription(appointment_id=appointment.id, patient_id=appointment.patient_id, doctor_id=doctor.id, **payload.model_dump())
    db.add(prescription); await db.commit(); await db.refresh(prescription)
    return prescription


@router.get("/prescriptions/me", response_model=List[PrescriptionResponse])
async def list_my_prescriptions(user: User = Depends(require_roles(UserRole.PATIENT)), db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(Prescription).where(Prescription.patient_id == user.id).order_by(Prescription.created_at.desc()))).scalars())
