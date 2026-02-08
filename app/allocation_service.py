from datetime import datetime, time, UTC, date
from typing import List, Optional
from app.crud.doctor import DoctorCRUD
from app.crud.slot import SlotCRUD
from app.crud.token import TokenCRUD
from app.models import TokenCreate, TokenSource, TokenStatus
from app.schemas import Slot, Token
from app.settings import settings


class AllocationService:
    def __init__(
        self, doctor_crud: DoctorCRUD, slot_crud: SlotCRUD, token_crud: TokenCRUD
    ):
        self.doctor_crud = doctor_crud
        self.slot_crud = slot_crud
        self.token_crud = token_crud

    def allocate_token(self, token_request: TokenCreate) -> Token:
        now = datetime.now(UTC)

        # normalize date
        request_date = (
            token_request.date.date()
            if isinstance(token_request.date, datetime)
            else token_request.date
        )

        with self.db.begin():

            # ---------- CASE 1: explicit slot ----------
            if token_request.slot_id:

                slot = self.slot_crud.get_slot_with_lock(token_request.slot_id)
                if not slot:
                    raise Exception("Slot not found")

                if slot.date != request_date:
                    raise Exception("Slot date mismatch")

                if request_date == now.date() and slot.start_time <= now.time():
                    raise Exception("Slot already started")

                active_count = self.token_crud.count_active_tokens(slot.id)

                max_capacity = slot.capacity
                if token_request.source == TokenSource.emergency:
                    max_capacity += settings.max_emergency_overflow

                if active_count >= max_capacity:
                    raise Exception("Slot full")

                token = Token(
                    doctor_id=token_request.doctor_id,
                    slot_id=slot.id,
                    source=token_request.source,
                    priority=self._priority(token_request.source),
                    status=TokenStatus.active,
                )

                self.db.add(token)
                return token

            # ---------- CASE 2: auto-assign nearest slot ----------
            slots = self.slot_crud.get_slots_for_doctor_by_date(
                token_request.doctor_id,
                request_date,
            )

            for slot in slots:
                if request_date == now.date() and slot.start_time <= now.time():
                    continue

                locked_slot = self.slot_crud.get_slot_with_lock(slot.id)

                active_count = self.token_crud.count_active_tokens(locked_slot.id)

                max_capacity = locked_slot.capacity
                if token_request.source == TokenSource.emergency:
                    max_capacity += settings.max_emergency_overflow

                if active_count < max_capacity:
                    token = Token(
                        doctor_id=token_request.doctor_id,
                        slot_id=locked_slot.id,
                        source=token_request.source,
                        priority=self._priority(token_request.source),
                        status=TokenStatus.active,
                    )

                    self.db.add(token)
                    return token

            # ---------- NO SLOT AVAILABLE ----------
            raise Exception("No available slot")

    def cancel_token(self, token_id: str) -> bool:
        """Cancel a token and reallocate if possible."""
        token = self.token_crud.get_token(token_id)
        if not token or token.status != TokenStatus.active:
            return False

        self.token_crud.update_token_status(token_id, TokenStatus.cancelled)

        # Reallocate for the slot
        if token.slot_id:
            self._reallocate_for_slot(token.slot_id)
        return True

    def mark_no_show(self, token_id: str) -> bool:
        """Mark token as no-show and reallocate."""
        token = self.token_crud.get_token(token_id)
        if not token or token.status != TokenStatus.active:
            return False

        self.token_crud.update_token_status(token_id, TokenStatus.no_show)

        # Reallocate for the slot
        if token.slot_id:
            self._reallocate_for_slot(token.slot_id)
        return True

    def serve_token(self, token_id: str) -> bool:
        """Mark token as served."""
        token = self.token_crud.get_token(token_id)
        if not token or token.status != TokenStatus.active:
            return False

        self.token_crud.update_token_status(token_id, TokenStatus.served)
        return True

    def _reallocate_for_slot(self, slot_id: str):
        """Reallocate waiting tokens to the slot if space available."""
        slot = self.slot_crud.get_slot(slot_id)
        if not slot:
            return

        active_tokens = self.token_crud.get_tokens_for_slot(slot_id)
        capacity = slot.capacity
        if any(t.source == TokenSource.emergency for t in active_tokens):
            capacity += settings.max_emergency_overflow

        if len(active_tokens) >= capacity:
            return  # No space

        # Get waiting tokens for the doctor on the same date as the slot
        doctor_id = slot.doctor_id
        slot_date = slot.date if isinstance(slot.date, date) else slot.date.date()
        waiting_tokens = self.token_crud.get_waiting_tokens_for_doctor_by_date(
            doctor_id, slot_date
        )

        for token in waiting_tokens:
            if len(active_tokens) < capacity:
                self.token_crud.assign_slot_to_token(token.id, slot_id)
                active_tokens.append(token)
            else:
                break

    def get_waiting_list(
        self, doctor_id: str, request_date: Optional[date] = None
    ) -> List[Token]:
        """Get waiting list for a doctor, optionally filtered by date."""
        if request_date:
            return self.token_crud.get_waiting_tokens_for_doctor_by_date(
                doctor_id, request_date
            )
        return self.token_crud.get_waiting_tokens_for_doctor(doctor_id)

    def get_slots_for_doctor(
        self, doctor_id: str, request_date: Optional[date] = None
    ) -> List[Slot]:
        """Get slots for a doctor, optionally filtered by date."""
        if request_date:
            slots = self.slot_crud.get_slots_for_doctor_by_date(doctor_id, request_date)
        else:
            slots = self.slot_crud.get_slots_for_doctor(doctor_id)

        result = []
        now = datetime.now(UTC)

        for slot in slots:
            slot_date = slot.date if isinstance(slot.date, date) else slot.date.date()
            # Include slots from future dates or future time slots for today
            if slot_date > now.date() or (
                slot_date == now.date() and slot.start_time >= now.time()
            ):
                result.append(slot)
        return result
