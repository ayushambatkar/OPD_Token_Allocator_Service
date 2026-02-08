from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from app.crud.main import OPDCRUD
from app.models import SlotCreate
from app.schemas import Slot


class SlotCRUD(OPDCRUD):
    def __init__(self):
        super().__init__()

    def create_slot(self, slot_data: SlotCreate, slot_date: date) -> Slot:
        """Create a new slot."""
        slot = Slot(
            doctor_id=str(slot_data.doctor_id),
            start_time=slot_data.start_time,
            end_time=slot_data.end_time,
            date=slot_date,
            capacity=slot_data.capacity,
        )
        self.db_session.add(slot)
        self.db_session.commit()
        self.db_session.refresh(slot)
        return slot

    def get_slot(self, slot_id: str) -> Optional[Slot]:
        """Get a slot by ID."""
        return self.db_session.query(Slot).filter(Slot.id == slot_id).first()

    def get_slot_with_lock(self, slot_id: str) -> Optional[Slot]:
        """Get a slot by ID with pessimistic lock (SELECT FOR UPDATE)."""
        return (
            self.db_session.query(Slot)
            .filter(Slot.id == slot_id)
            .with_for_update()
            .first()
        )

    def get_slots_for_doctor(self, doctor_id: str) -> List[Slot]:
        """Get all slots for a doctor."""
        return (
            self.db_session.query(Slot)
            .filter(Slot.doctor_id == doctor_id)
            .order_by(Slot.date, Slot.start_time)
            .all()
        )

    def get_slots_for_doctor_by_date(
        self, doctor_id: str, request_date: date
    ) -> List[Slot]:
        """Get slots for a doctor on a specific date."""
        from sqlalchemy import func, cast, Date

        return (
            self.db_session.query(Slot)
            .filter(Slot.doctor_id == doctor_id, cast(Slot.date, Date) == request_date)
            .order_by(Slot.start_time)
            .all()
        )

    def delete_slot(self, slot_id: str) -> bool:
        """Delete a slot."""
        slot = self.get_slot(slot_id)
        if slot:
            self.db_session.delete(slot)
            self.db_session.commit()
            return True
        return False
