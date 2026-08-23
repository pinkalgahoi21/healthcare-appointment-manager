from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.doctor import DoctorProfile, DoctorWorkingHours
from app.models.appointment_slot import AppointmentSlot, SlotStatus
from app.models.doctor_leave import DoctorLeave, LeaveStatus
from app.schemas.slot import DoctorAvailabilityResponse, SlotResponse


class SlotService:
    @staticmethod
    async def is_doctor_on_leave(
        db: AsyncSession,
        doctor_id: UUID,
        target_date: date,
    ) -> Optional[DoctorLeave]:
        """
        Checks if the doctor has an approved leave overlapping target_date.
        """
        stmt = (
            select(DoctorLeave)
            .where(
                and_(
                    DoctorLeave.doctor_id == doctor_id,
                    DoctorLeave.status == LeaveStatus.APPROVED.value,
                    DoctorLeave.leave_date <= target_date,
                    or_(
                        DoctorLeave.end_date == None,
                        DoctorLeave.end_date >= target_date,
                    ),
                )
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def generate_slots_for_date(
        db: AsyncSession,
        doctor_id: UUID,
        target_date: date,
    ) -> List[AppointmentSlot]:
        """
        Generates and persists discrete appointment slots for a doctor on target_date
        according to their working hours and slot duration. Idempotent.
        """
        # 1. Fetch doctor profile
        doc_stmt = select(DoctorProfile).where(DoctorProfile.id == doctor_id)
        doc_result = await db.execute(doc_stmt)
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            return []

        # 2. Check if on leave
        leave = await SlotService.is_doctor_on_leave(db, doctor_id, target_date)
        if leave:
            # Query any existing slots and mark as unavailable if needed
            existing_stmt = (
                select(AppointmentSlot)
                .where(
                    and_(
                        AppointmentSlot.doctor_id == doctor_id,
                        AppointmentSlot.slot_date == target_date,
                    )
                )
                .order_by(AppointmentSlot.start_time)
            )
            existing_res = await db.execute(existing_stmt)
            return list(existing_res.scalars().all())

        # 3. Check working hours for day of week (Python weekday: 0=Monday .. 6=Sunday)
        day_of_week = target_date.weekday()
        wh_stmt = (
            select(DoctorWorkingHours)
            .where(
                and_(
                    DoctorWorkingHours.doctor_id == doctor_id,
                    DoctorWorkingHours.day_of_week == day_of_week,
                    DoctorWorkingHours.is_active == True,
                )
            )
        )
        wh_result = await db.execute(wh_stmt)
        working_shifts = list(wh_result.scalars().all())
        if not working_shifts:
            return []

        # 4. Fetch already existing slots on target_date to avoid duplicates
        existing_stmt = (
            select(AppointmentSlot)
            .where(
                and_(
                    AppointmentSlot.doctor_id == doctor_id,
                    AppointmentSlot.slot_date == target_date,
                )
            )
        )
        existing_res = await db.execute(existing_stmt)
        existing_slots = list(existing_res.scalars().all())

        def _norm(dt: datetime) -> str:
            if dt.tzinfo:
                return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            return dt.strftime("%Y-%m-%d %H:%M:%S")

        existing_starts = {_norm(s.start_time) for s in existing_slots}

        slot_duration = timedelta(minutes=doctor.slot_duration_minutes)
        new_slots: List[AppointmentSlot] = []

        for shift in working_shifts:
            # Construct start and end datetimes in UTC for this date
            shift_start = datetime.combine(target_date, shift.start_time, tzinfo=timezone.utc)
            shift_end = datetime.combine(target_date, shift.end_time, tzinfo=timezone.utc)

            curr = shift_start
            while curr + slot_duration <= shift_end:
                slot_end = curr + slot_duration
                if _norm(curr) not in existing_starts:
                    slot = AppointmentSlot(
                        doctor_id=doctor_id,
                        slot_date=target_date,
                        start_time=curr,
                        end_time=slot_end,
                        status=SlotStatus.AVAILABLE.value,
                    )
                    db.add(slot)
                    new_slots.append(slot)
                    existing_starts.add(_norm(curr))
                curr = slot_end

        if new_slots:
            await db.commit()

        # 5. Return all slots for this date ordered by start_time
        final_stmt = (
            select(AppointmentSlot)
            .where(
                and_(
                    AppointmentSlot.doctor_id == doctor_id,
                    AppointmentSlot.slot_date == target_date,
                )
            )
            .order_by(AppointmentSlot.start_time)
        )
        final_res = await db.execute(final_stmt)
        return list(final_res.scalars().all())

    @staticmethod
    async def get_availability(
        db: AsyncSession,
        doctor_id: UUID,
        target_date: date,
    ) -> DoctorAvailabilityResponse:
        """
        Retrieves doctor availability for a given date, automatically generating slots if needed.
        """
        doc_stmt = select(DoctorProfile).where(DoctorProfile.id == doctor_id)
        doc_result = await db.execute(doc_stmt)
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            return DoctorAvailabilityResponse(
                doctor_id=doctor_id,
                date=target_date,
                slot_duration_minutes=30,
                is_on_leave=False,
                slots=[],
            )

        leave = await SlotService.is_doctor_on_leave(db, doctor_id, target_date)
        is_on_leave = leave is not None
        leave_reason = leave.reason if leave else None

        slots = await SlotService.generate_slots_for_date(db, doctor_id, target_date)
        slot_dtos = [
            SlotResponse(
                id=s.id,
                doctor_id=s.doctor_id,
                slot_date=s.slot_date,
                start_time=s.start_time,
                end_time=s.end_time,
                status=SlotStatus(s.status),
            )
            for s in slots
        ]

        return DoctorAvailabilityResponse(
            doctor_id=doctor_id,
            date=target_date,
            slot_duration_minutes=doctor.slot_duration_minutes,
            is_on_leave=is_on_leave,
            leave_reason=leave_reason,
            slots=slot_dtos,
        )

    @staticmethod
    async def get_slot_by_id(
        db: AsyncSession,
        slot_id: UUID,
    ) -> Optional[AppointmentSlot]:
        stmt = select(AppointmentSlot).where(AppointmentSlot.id == slot_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
