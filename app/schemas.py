"""
Contains DB Schemas
"""

from datetime import datetime, UTC
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Time

from app.db import Base, engine
from app.models import TokenSource, TokenStatus


class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class Slot(Base):
    __tablename__ = "slots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    date = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class Token(Base):
    __tablename__ = "tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    slot_id = Column(String(36), ForeignKey("slots.id"), nullable=True)
    source = Column(Enum(TokenSource), nullable=False)
    status = Column(Enum(TokenStatus), nullable=False, default=TokenStatus.active)
    priority = Column(Integer)
    patient_name = Column(String, nullable=False)
    patient_contact = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


Base.metadata.create_all(bind=engine)
