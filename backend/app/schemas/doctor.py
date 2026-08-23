from typing import Optional, List
from uuid import UUID
from datetime import date, time, datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


class WorkingHoursItem(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday ... 6=Sunday")
    start_time: time
    end_time: time
    is_active: bool = True

    @field_validator("end_time")
    @classmethod
    def validate_times(cls, end_time: time, info):
        start_time = info.data.get("start_time")
        if start_time and end_time <= start_time:
            raise ValueError("end_time must be strictly after start_time")
        return end_time


class WorkingHoursSetRequest(BaseModel):
    working_hours: List[WorkingHoursItem]


class WorkingHoursResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    doctor_id: UUID
    day_of_week: int
    start_time: time
    end_time: time
    is_active: bool


class DoctorCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    specialization: str = Field(..., min_length=2, max_length=100)
    bio: Optional[str] = None
    slot_duration_minutes: int = Field(30, gt=0, le=240)
    consultation_fee: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"))
    phone: Optional[str] = Field(None, max_length=20)


class DoctorUpdateRequest(BaseModel):
    specialization: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = None
    slot_duration_minutes: Optional[int] = Field(None, gt=0, le=240)
    consultation_fee: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    phone: Optional[str] = Field(None, max_length=20)


class DoctorProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    email: str
    specialization: str
    bio: Optional[str] = None
    slot_duration_minutes: int
    consultation_fee: Decimal
    phone: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    working_hours: List[WorkingHoursResponse] = []


class SpecializationListResponse(BaseModel):
    specializations: List[str]


class DoctorLeaveCreateRequest(BaseModel):
    doctor_id: UUID
    leave_date: date
    end_date: Optional[date] = None
    reason: Optional[str] = Field(None, max_length=255)

    @field_validator("end_date")
    @classmethod
    def validate_range(cls, end_date: Optional[date], info):
        start = info.data.get("leave_date")
        if start and end_date and end_date < start:
            raise ValueError("end_date cannot be earlier than leave_date")
        return end_date


class DoctorLeaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    doctor_id: UUID
    leave_date: date
    end_date: Optional[date]
    reason: Optional[str]
    status: str
    created_at: datetime
