"""Concurrency-safe slot holds and appointment bookings."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.appointment import Appointment, AppointmentStatus
from app.models.appointment_slot import AppointmentSlot, SlotStatus
from app.models.doctor import DoctorProfile
from app.models.doctor_leave import DoctorLeave, LeaveStatus
from app.models.slot_hold import SlotHold, SlotHoldStatus
from app.models.outbox_event import OutboxEvent


def _utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class BookingService:
    @staticmethod
    async def _slot(db: AsyncSession, slot_id: UUID) -> AppointmentSlot:
        slot = (await db.execute(select(AppointmentSlot).where(AppointmentSlot.id == slot_id).with_for_update())).scalar_one_or_none()
        if not slot:
            raise HTTPException(status_code=404, detail=f"Appointment slot '{slot_id}' not found.")
        return slot

    @staticmethod
    async def _on_leave(db: AsyncSession, slot: AppointmentSlot) -> bool:
        query = select(DoctorLeave.id).where(
            DoctorLeave.doctor_id == slot.doctor_id,
            DoctorLeave.status == LeaveStatus.APPROVED.value,
            DoctorLeave.leave_date <= slot.slot_date,
            or_(DoctorLeave.end_date.is_(None), DoctorLeave.end_date >= slot.slot_date),
        )
        return (await db.execute(query)).scalar_one_or_none() is not None

    @staticmethod
    async def _expire_holds(db: AsyncSession, slot: AppointmentSlot, now: datetime) -> Optional[SlotHold]:
        holds = (await db.execute(
            select(SlotHold).where(SlotHold.slot_id == slot.id, SlotHold.status == SlotHoldStatus.ACTIVE.value).with_for_update()
        )).scalars().all()
        live = None
        for hold in holds:
            if _utc(hold.expires_at) <= now:
                hold.status = SlotHoldStatus.EXPIRED.value
            else:
                live = hold
        if live is None and slot.status == SlotStatus.HELD.value:
            slot.status = SlotStatus.AVAILABLE.value
            slot.held_by_user_id = None
            slot.held_until = None
        return live

    @staticmethod
    def _available(slot: AppointmentSlot, now: datetime) -> None:
        if _utc(slot.start_time) <= now:
            raise HTTPException(status_code=409, detail="Past appointment slots cannot be booked.")
        if slot.status != SlotStatus.AVAILABLE.value:
            raise HTTPException(status_code=409, detail="Slot is not available for booking.")

    @staticmethod
    async def hold_slot(db: AsyncSession, slot_id: UUID, user_id: UUID, chief_complaint: Optional[str] = None) -> SlotHold:
        now = datetime.now(timezone.utc)
        slot = await BookingService._slot(db, slot_id)
        live = await BookingService._expire_holds(db, slot, now)
        if live:
            if live.patient_id == user_id:
                return live
            raise HTTPException(status_code=409, detail="Slot is currently held by another patient.")
        BookingService._available(slot, now)
        if await BookingService._on_leave(db, slot):
            raise HTTPException(status_code=409, detail="The doctor is unavailable on this date.")
        hold = SlotHold(slot_id=slot.id, patient_id=user_id, status=SlotHoldStatus.ACTIVE.value,
                        expires_at=now + timedelta(minutes=settings.SLOT_HOLD_DURATION_MINUTES))
        slot.status = SlotStatus.HELD.value
        slot.held_by_user_id = user_id
        slot.held_until = hold.expires_at
        db.add(hold)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="Slot is currently held by another patient.")
        await db.refresh(hold)
        return hold

    @staticmethod
    async def confirm_appointment(db: AsyncSession, appointment_id: UUID, user_id: UUID,
                                  chief_complaint: Optional[str] = None) -> Appointment:
        now = datetime.now(timezone.utc)
        # Read the slot id first, then acquire locks in the same order as
        # hold_slot: slot followed by hold. This avoids a slot/hold deadlock.
        hold = (await db.execute(select(SlotHold).where(SlotHold.id == appointment_id))).scalar_one_or_none()
        if not hold:
            raise HTTPException(status_code=404, detail=f"Slot hold '{appointment_id}' not found.")
        if hold.patient_id != user_id:
            raise HTTPException(status_code=403, detail="You do not have permission to confirm this slot hold.")
        slot = await BookingService._slot(db, hold.slot_id)
        hold = (await db.execute(select(SlotHold).where(SlotHold.id == appointment_id).with_for_update())).scalar_one_or_none()
        if not hold:
            raise HTTPException(status_code=404, detail=f"Slot hold '{appointment_id}' not found.")
        await BookingService._expire_holds(db, slot, now)
        if hold.status != SlotHoldStatus.ACTIVE.value:
            if hold.status == SlotHoldStatus.EXPIRED.value:
                await db.commit()
            raise HTTPException(status_code=409, detail="The slot hold is no longer active.")
        if _utc(slot.start_time) <= now or slot.status in (SlotStatus.UNAVAILABLE.value, SlotStatus.BOOKED.value):
            raise HTTPException(status_code=409, detail="Slot is no longer available for confirmation.")
        if await BookingService._on_leave(db, slot):
            raise HTTPException(status_code=409, detail="The doctor is unavailable on this date.")
        appointment = Appointment(patient_id=user_id, doctor_id=slot.doctor_id, slot_id=slot.id,
                                  status=AppointmentStatus.CONFIRMED.value, chief_complaint=chief_complaint,
                                  booked_at=now, confirmed_at=now)
        hold.status = SlotHoldStatus.CONVERTED.value
        slot.status = SlotStatus.BOOKED.value
        slot.held_by_user_id = None
        slot.held_until = None
        db.add(appointment)
        await db.flush()
        db.add(OutboxEvent(
            event_type="APPOINTMENT_CONFIRMED", aggregate_type="appointment", aggregate_id=appointment.id,
            payload={"appointment_id": str(appointment.id), "patient_id": str(user_id), "slot_id": str(slot.id)},
            idempotency_key=f"appointment-confirmed:{appointment.id}",
        ))
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="Slot has already been booked.")
        await db.refresh(appointment)
        return appointment

    @staticmethod
    async def release_hold(db: AsyncSession, hold_id: UUID, user_id: UUID) -> SlotHold:
        hold = (await db.execute(select(SlotHold).where(SlotHold.id == hold_id).with_for_update())).scalar_one_or_none()
        if not hold:
            raise HTTPException(status_code=404, detail=f"Slot hold '{hold_id}' not found.")
        if hold.patient_id != user_id:
            raise HTTPException(status_code=403, detail="You can only release your own slot hold.")
        if hold.status != SlotHoldStatus.ACTIVE.value:
            raise HTTPException(status_code=409, detail="Only active slot holds can be released.")
        slot = await BookingService._slot(db, hold.slot_id)
        hold.status = SlotHoldStatus.RELEASED.value
        if slot.status == SlotStatus.HELD.value:
            slot.status = SlotStatus.AVAILABLE.value
        await db.commit()
        await db.refresh(hold)
        return hold

    @staticmethod
    async def cancel_appointment(db: AsyncSession, appointment_id: UUID, user_id: UUID, user_role: str,
                                 reason: Optional[str] = None) -> Appointment:
        now = datetime.now(timezone.utc)
        appointment = (await db.execute(select(Appointment).where(Appointment.id == appointment_id).with_for_update())).scalar_one_or_none()
        if not appointment:
            raise HTTPException(status_code=404, detail=f"Appointment '{appointment_id}' not found.")
        if user_role == "PATIENT" and appointment.patient_id != user_id:
            raise HTTPException(status_code=403, detail="You can only cancel your own appointments.")
        if user_role == "DOCTOR":
            doctor = (await db.execute(select(DoctorProfile).where(DoctorProfile.user_id == user_id))).scalar_one_or_none()
            if not doctor or doctor.id != appointment.doctor_id:
                raise HTTPException(status_code=403, detail="Doctors can only cancel their own appointments.")
        if appointment.status in (AppointmentStatus.CANCELLED.value, AppointmentStatus.COMPLETED.value):
            raise HTTPException(status_code=409, detail=f"Cannot cancel appointment already in '{appointment.status}' status.")
        slot = await BookingService._slot(db, appointment.slot_id)
        appointment.status, appointment.cancelled_at, appointment.cancellation_reason = AppointmentStatus.CANCELLED.value, now, reason
        slot.status = SlotStatus.AVAILABLE.value
        db.add(OutboxEvent(event_type="APPOINTMENT_CANCELLED", aggregate_type="appointment", aggregate_id=appointment.id,
            payload={"appointment_id": str(appointment.id)}, idempotency_key=f"appointment-cancelled:{appointment.id}"))
        await db.commit()
        await db.refresh(appointment)
        return appointment

    @staticmethod
    async def list_patient_appointments(db: AsyncSession, patient_id: UUID, appointment_status: Optional[str] = None) -> List[Appointment]:
        q = select(Appointment).where(Appointment.patient_id == patient_id)
        if appointment_status: q = q.where(Appointment.status == appointment_status)
        return list((await db.execute(q.order_by(Appointment.created_at.desc()))).scalars())

    @staticmethod
    async def list_doctor_appointments(db: AsyncSession, doctor_id: UUID, appointment_status: Optional[str] = None) -> List[Appointment]:
        q = select(Appointment).where(Appointment.doctor_id == doctor_id)
        if appointment_status: q = q.where(Appointment.status == appointment_status)
        return list((await db.execute(q.order_by(Appointment.created_at.desc()))).scalars())

    @staticmethod
    async def complete_appointment(db: AsyncSession, appointment_id: UUID, doctor_id: UUID) -> Appointment:
        appointment = (await db.execute(select(Appointment).where(Appointment.id == appointment_id).with_for_update())).scalar_one_or_none()
        if not appointment: raise HTTPException(status_code=404, detail="Appointment not found.")
        if appointment.doctor_id != doctor_id: raise HTTPException(status_code=403, detail="Only the attending doctor may complete this appointment.")
        if appointment.status != AppointmentStatus.CONFIRMED.value: raise HTTPException(status_code=409, detail="Only confirmed appointments can be completed.")
        appointment.status, appointment.completed_at = AppointmentStatus.COMPLETED.value, datetime.now(timezone.utc)
        await db.commit(); await db.refresh(appointment)
        return appointment

    @staticmethod
    async def mark_reschedule_required(db: AsyncSession, appointment_id: UUID, doctor_id: UUID) -> Appointment:
        appointment = (await db.execute(select(Appointment).where(Appointment.id == appointment_id).with_for_update())).scalar_one_or_none()
        if not appointment: raise HTTPException(status_code=404, detail="Appointment not found.")
        if appointment.doctor_id != doctor_id: raise HTTPException(status_code=403, detail="Only the attending doctor may flag this appointment for rescheduling.")
        if appointment.status != AppointmentStatus.CONFIRMED.value: raise HTTPException(status_code=409, detail="Only confirmed appointments can require rescheduling.")
        slot = await BookingService._slot(db, appointment.slot_id)
        appointment.status, slot.status = AppointmentStatus.RESCHEDULED_REQUIRED.value, SlotStatus.AVAILABLE.value
        db.add(OutboxEvent(event_type="APPOINTMENT_RESCHEDULE_REQUIRED", aggregate_type="appointment", aggregate_id=appointment.id,
            payload={"appointment_id": str(appointment.id)}, idempotency_key=f"appointment-reschedule:{appointment.id}"))
        await db.commit(); await db.refresh(appointment)
        return appointment

    @staticmethod
    async def get_appointment_by_id(db: AsyncSession, appointment_id: UUID) -> Optional[Appointment]:
        return (await db.execute(select(Appointment).where(Appointment.id == appointment_id))).scalar_one_or_none()

    @staticmethod
    async def release_expired_holds(db: AsyncSession) -> int:
        now = datetime.now(timezone.utc)
        holds = (await db.execute(select(SlotHold).where(SlotHold.status == SlotHoldStatus.ACTIVE.value,
                                  SlotHold.expires_at <= now).with_for_update(skip_locked=True))).scalars().all()
        for hold in holds:
            hold.status = SlotHoldStatus.EXPIRED.value
            slot = await BookingService._slot(db, hold.slot_id)
            if slot.status == SlotStatus.HELD.value: slot.status = SlotStatus.AVAILABLE.value
        if holds: await db.commit()
        return len(holds)
