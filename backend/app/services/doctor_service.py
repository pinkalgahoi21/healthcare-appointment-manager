from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, distinct, or_
from sqlalchemy.orm import selectinload, joinedload
from app.models.user import User, UserRole
from app.models.doctor import DoctorProfile, DoctorWorkingHours
from app.schemas.doctor import (
    DoctorCreateRequest,
    DoctorUpdateRequest,
    DoctorProfileResponse,
    WorkingHoursItem,
    WorkingHoursResponse,
)
from app.services.user_service import UserService


class DoctorService:
    @staticmethod
    def to_response_dto(profile: DoctorProfile) -> DoctorProfileResponse:
        """Converts DoctorProfile ORM instance to DoctorProfileResponse Pydantic schema."""
        user = profile.user
        wh_dtos = [
            WorkingHoursResponse(
                id=wh.id,
                doctor_id=wh.doctor_id,
                day_of_week=wh.day_of_week,
                start_time=wh.start_time,
                end_time=wh.end_time,
                is_active=wh.is_active,
            )
            for wh in (profile.working_hours or [])
        ]
        return DoctorProfileResponse(
            id=profile.id,
            user_id=profile.user_id,
            name=user.name if user else "Unknown Doctor",
            email=user.email if user else "",
            specialization=profile.specialization,
            bio=profile.bio,
            slot_duration_minutes=profile.slot_duration_minutes,
            consultation_fee=profile.consultation_fee,
            phone=user.phone if user else None,
            is_active=user.is_active if user else True,
            created_at=profile.created_at,
            working_hours=wh_dtos,
        )

    @staticmethod
    async def get_by_id(db: AsyncSession, doctor_id: UUID) -> Optional[DoctorProfile]:
        stmt = (
            select(DoctorProfile)
            .where(DoctorProfile.id == doctor_id)
            .options(joinedload(DoctorProfile.user), selectinload(DoctorProfile.working_hours))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: UUID) -> Optional[DoctorProfile]:
        stmt = (
            select(DoctorProfile)
            .where(DoctorProfile.user_id == user_id)
            .options(joinedload(DoctorProfile.user), selectinload(DoctorProfile.working_hours))
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_doctor(
        db: AsyncSession,
        payload: DoctorCreateRequest,
    ) -> DoctorProfile:
        # Create underlying user with DOCTOR role
        user = await UserService.create_user(
            db=db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role=UserRole.DOCTOR,
            phone=payload.phone,
        )

        doctor_profile = DoctorProfile(
            user_id=user.id,
            specialization=payload.specialization.strip(),
            bio=payload.bio.strip() if payload.bio else None,
            slot_duration_minutes=payload.slot_duration_minutes,
            consultation_fee=payload.consultation_fee,
        )
        db.add(doctor_profile)
        await db.commit()
        await db.refresh(doctor_profile)

        # Reload with user relationship
        return await DoctorService.get_by_id(db, doctor_profile.id)

    @staticmethod
    async def update_doctor(
        db: AsyncSession,
        doctor_id: UUID,
        payload: DoctorUpdateRequest,
    ) -> Optional[DoctorProfile]:
        profile = await DoctorService.get_by_id(db, doctor_id)
        if not profile:
            return None

        if payload.specialization is not None:
            profile.specialization = payload.specialization.strip()
        if payload.bio is not None:
            profile.bio = payload.bio.strip()
        if payload.slot_duration_minutes is not None:
            profile.slot_duration_minutes = payload.slot_duration_minutes
        if payload.consultation_fee is not None:
            profile.consultation_fee = payload.consultation_fee

        if payload.phone is not None and profile.user:
            profile.user.phone = payload.phone.strip()

        await db.commit()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def list_doctors(
        db: AsyncSession,
        specialization: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DoctorProfile]:
        stmt = (
            select(DoctorProfile)
            .join(User, DoctorProfile.user_id == User.id)
            .options(joinedload(DoctorProfile.user), selectinload(DoctorProfile.working_hours))
            .where(User.is_active == True)
        )

        if specialization:
            stmt = stmt.where(DoctorProfile.specialization.ilike(f"%{specialization.strip()}%"))

        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    User.name.ilike(pattern),
                    DoctorProfile.specialization.ilike(pattern),
                    DoctorProfile.bio.ilike(pattern),
                )
            )

        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def list_specializations(db: AsyncSession) -> List[str]:
        stmt = (
            select(distinct(DoctorProfile.specialization))
            .order_by(DoctorProfile.specialization)
        )
        result = await db.execute(stmt)
        return [r for r in result.scalars().all() if r]

    @staticmethod
    async def set_working_hours(
        db: AsyncSession,
        doctor_id: UUID,
        items: List[WorkingHoursItem],
    ) -> List[DoctorWorkingHours]:
        # Delete existing working hours for doctor
        await db.execute(
            delete(DoctorWorkingHours).where(DoctorWorkingHours.doctor_id == doctor_id)
        )

        created_records = []
        for item in items:
            wh = DoctorWorkingHours(
                doctor_id=doctor_id,
                day_of_week=item.day_of_week,
                start_time=item.start_time,
                end_time=item.end_time,
                is_active=item.is_active,
            )
            db.add(wh)
            created_records.append(wh)

        await db.commit()
        for r in created_records:
            await db.refresh(r)
        return created_records

    @staticmethod
    async def get_working_hours(
        db: AsyncSession,
        doctor_id: UUID,
    ) -> List[DoctorWorkingHours]:
        stmt = (
            select(DoctorWorkingHours)
            .where(DoctorWorkingHours.doctor_id == doctor_id)
            .order_by(DoctorWorkingHours.day_of_week, DoctorWorkingHours.start_time)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
