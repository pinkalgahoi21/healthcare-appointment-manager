from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.models.appointment_slot import AppointmentSlot, SlotStatus
from app.models.doctor_leave import DoctorLeave, LeaveStatus
from app.models.outbox_event import OutboxEvent
from app.models.slot_hold import SlotHold, SlotHoldStatus


class LeaveService:
    @staticmethod
    async def create(db: AsyncSession, doctor_id: UUID, leave_date, end_date, reason: str | None) -> DoctorLeave:
        end_date = end_date or leave_date
        overlapping = (await db.execute(select(DoctorLeave.id).where(
            DoctorLeave.doctor_id == doctor_id, DoctorLeave.status == LeaveStatus.APPROVED.value,
            DoctorLeave.leave_date <= end_date, or_(DoctorLeave.end_date.is_(None), DoctorLeave.end_date >= leave_date),
        ))).scalar_one_or_none()
        if overlapping:
            raise HTTPException(status_code=409, detail="An approved leave already overlaps this date range.")
        leave = DoctorLeave(doctor_id=doctor_id, leave_date=leave_date, end_date=end_date, reason=reason, status=LeaveStatus.APPROVED.value)
        db.add(leave)
        slots = (await db.execute(select(AppointmentSlot).where(
            AppointmentSlot.doctor_id == doctor_id, AppointmentSlot.slot_date >= leave_date, AppointmentSlot.slot_date <= end_date,
        ).with_for_update())).scalars().all()
        now = datetime.now(timezone.utc)
        for slot in slots:
            slot.status = SlotStatus.UNAVAILABLE.value
            holds = (await db.execute(select(SlotHold).where(SlotHold.slot_id == slot.id, SlotHold.status == SlotHoldStatus.ACTIVE.value).with_for_update())).scalars()
            for hold in holds:
                hold.status = SlotHoldStatus.RELEASED.value
            appointments = (await db.execute(select(Appointment).where(
                Appointment.slot_id == slot.id, Appointment.status == AppointmentStatus.CONFIRMED.value).with_for_update())).scalars()
            for appointment in appointments:
                appointment.status = AppointmentStatus.RESCHEDULED_REQUIRED.value
                db.add(OutboxEvent(event_type="APPOINTMENT_RESCHEDULE_REQUIRED", aggregate_type="appointment", aggregate_id=appointment.id,
                    payload={"appointment_id": str(appointment.id), "reason": "doctor_leave"}, idempotency_key=f"leave:{leave.id}:appointment:{appointment.id}"))
        await db.commit()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def list(db: AsyncSession, doctor_id: UUID | None = None):
        query = select(DoctorLeave).order_by(DoctorLeave.leave_date.desc())
        if doctor_id:
            query = query.where(DoctorLeave.doctor_id == doctor_id)
        return list((await db.execute(query)).scalars())

    @staticmethod
    async def remove(db: AsyncSession, leave_id: UUID) -> DoctorLeave:
        leave = (await db.execute(select(DoctorLeave).where(DoctorLeave.id == leave_id).with_for_update())).scalar_one_or_none()
        if not leave:
            raise HTTPException(status_code=404, detail="Doctor leave not found.")
        leave.status = LeaveStatus.CANCELLED.value
        await db.commit()
        await db.refresh(leave)
        return leave
