from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models.appointment import Appointment
from app.models.clinical import ClinicalNote, PostVisitSummary, Prescription
from app.models.doctor import DoctorProfile
from app.models.engagement import MedicationReminder, Notification
from app.models.user import User, UserRole
from app.schemas.engagement import (NotificationResponse, PostVisitRequest, PostVisitSummaryResponse,
                                    PreVisitSummaryResponse, ReminderCreate, ReminderResponse, SymptomsRequest)
from app.services.ai_service import AiSummaryService

router = APIRouter(tags=["Patient engagement"])


async def _appointment_for_patient(db: AsyncSession, appointment_id: UUID, user_id: UUID) -> Appointment:
    appointment = (await db.execute(select(Appointment).where(Appointment.id == appointment_id))).scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if appointment.patient_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return appointment


async def _appointment_for_doctor(db: AsyncSession, appointment_id: UUID, user_id: UUID) -> Appointment:
    doctor = (await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user_id))).scalar_one_or_none()
    appointment = (await db.execute(select(Appointment).where(Appointment.id == appointment_id))).scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    if not doctor or appointment.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return appointment


@router.post("/appointments/{appointment_id}/pre-visit-summary", response_model=PreVisitSummaryResponse)
async def pre_visit_summary(appointment_id: UUID, payload: SymptomsRequest, user: User = Depends(require_roles(UserRole.PATIENT)), db: AsyncSession = Depends(get_db)):
    appointment = await _appointment_for_patient(db, appointment_id, user.id)
    appointment.chief_complaint = payload.symptoms
    await db.commit()
    return await AiSummaryService.pre_visit(payload.symptoms)


@router.post("/appointments/{appointment_id}/post-visit-summary", response_model=PostVisitSummaryResponse)
async def create_post_visit_summary(appointment_id: UUID, payload: PostVisitRequest, user: User = Depends(require_roles(UserRole.DOCTOR)), db: AsyncSession = Depends(get_db)):
    appointment = await _appointment_for_doctor(db, appointment_id, user.id)
    doctor = (await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))).scalar_one()
    note = (await db.execute(select(ClinicalNote).where(ClinicalNote.appointment_id == appointment.id))).scalar_one_or_none()
    prescriptions = list((await db.execute(select(Prescription).where(Prescription.appointment_id == appointment.id))).scalars())
    content = await AiSummaryService.post_visit(note.content if note else "", [{"medication_name": p.medication_name, "dosage": p.dosage, "frequency": p.frequency, "instructions": p.instructions} for p in prescriptions], payload.follow_up_instructions)
    summary = (await db.execute(select(PostVisitSummary).where(PostVisitSummary.appointment_id == appointment.id))).scalar_one_or_none()
    if summary:
        summary.content, summary.is_published = content, False
    else:
        summary = PostVisitSummary(appointment_id=appointment.id, doctor_id=doctor.id, content=content)
        db.add(summary)
    await db.commit(); await db.refresh(summary)
    return summary


@router.post("/post-visit-summaries/{summary_id}/publish", response_model=PostVisitSummaryResponse)
async def publish_summary(summary_id: UUID, user: User = Depends(require_roles(UserRole.DOCTOR)), db: AsyncSession = Depends(get_db)):
    summary = (await db.execute(select(PostVisitSummary).where(PostVisitSummary.id == summary_id))).scalar_one_or_none()
    doctor = (await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user.id))).scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found.")
    if not doctor or summary.doctor_id != doctor.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    summary.is_published = True
    await db.commit(); await db.refresh(summary)
    return summary


@router.get("/appointments/{appointment_id}/post-visit-summary", response_model=PostVisitSummaryResponse)
async def patient_summary(appointment_id: UUID, user: User = Depends(require_roles(UserRole.PATIENT)), db: AsyncSession = Depends(get_db)):
    await _appointment_for_patient(db, appointment_id, user.id)
    summary = (await db.execute(select(PostVisitSummary).where(PostVisitSummary.appointment_id == appointment_id, PostVisitSummary.is_published.is_(True)))).scalar_one_or_none()
    if not summary:
        raise HTTPException(status_code=404, detail="Published summary not found.")
    return summary


@router.get("/notifications/me", response_model=List[NotificationResponse])
async def notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()))).scalars())


@router.post("/reminders", response_model=ReminderResponse)
async def create_reminder(payload: ReminderCreate, user: User = Depends(require_roles(UserRole.PATIENT)), db: AsyncSession = Depends(get_db)):
    prescription = (await db.execute(select(Prescription).where(Prescription.id == payload.prescription_id))).scalar_one_or_none()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found.")
    if prescription.patient_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    reminder = MedicationReminder(patient_id=user.id, **payload.model_dump())
    db.add(reminder); await db.commit(); await db.refresh(reminder)
    return reminder


@router.get("/reminders/me", response_model=List[ReminderResponse])
async def reminders(user: User = Depends(require_roles(UserRole.PATIENT)), db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(MedicationReminder).where(MedicationReminder.patient_id == user.id).order_by(MedicationReminder.created_at.desc()))).scalars())
