import enum
import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime, time
from enum import Enum, IntEnum
from typing import Optional


class TokenSource(str, enum.Enum):
    online = "online"
    walk_in = "walk_in"
    paid = "paid"
    follow_up = "follow_up"
    emergency = "emergency"


class TokenStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    served = "served"
    no_show = "no_show"
    displaced = "displaced"
    waiting = "waiting"


class TokenPriority(IntEnum):
    EMERGENCY = 1
    PAID = 2
    FOLLOW_UP = 3
    WALK_IN = 4
    ONLINE = 5


# ---------- Doctor ----------


class DoctorCreate(BaseModel):
    name: str
    specialization: str


class DoctorResponse(DoctorCreate):
    id: uuid.UUID

    class Config:
        from_attributes = True


# ---------- Slot ----------


class SlotCreate(BaseModel):
    doctor_id: uuid.UUID
    start_time: time
    end_time: time
    capacity: int


class SlotResponse(SlotCreate):
    id: uuid.UUID

    class Config:
        from_attributes = True


# ---------- Token ----------


class TokenCreate(BaseModel):
    doctor_id: uuid.UUID
    slot_id: Optional[uuid.UUID]
    date: datetime
    source: TokenSource
    patient_name: str
    patient_contact: str


class TokenResponse(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    slot_id: Optional[uuid.UUID]
    source: TokenSource
    priority: int
    status: TokenStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
