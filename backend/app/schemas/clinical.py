from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ClinicalNoteUpsert(BaseModel):
    content: str = Field(min_length=1, max_length=20000)


class ClinicalNoteResponse(ClinicalNoteUpsert):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    appointment_id: UUID
    doctor_id: UUID
    updated_at: datetime


class PrescriptionCreate(BaseModel):
    medication_name: str = Field(min_length=1, max_length=200)
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=1, max_length=100)
    instructions: Optional[str] = Field(None, max_length=5000)


class PrescriptionResponse(PrescriptionCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    appointment_id: UUID
    patient_id: UUID
    doctor_id: UUID
    active: bool
    created_at: datetime
