from datetime import datetime, time, UTC, date
from typing import List, Optional
from app.crud.doctor import DoctorCRUD
from app.crud.slot import SlotCRUD
from app.crud.token import TokenCRUD
from app.models import TokenCreate, TokenSource, TokenStatus
from app.schemas import Doctor, Slot, Token
from app.settings import settings


class AllocationService:
    def __init__(
        self, doctor_crud: DoctorCRUD, slot_crud: SlotCRUD, token_crud: TokenCRUD
    ):
        self.doctor_crud = doctor_crud
        self.slot_crud = slot_crud
        self.token_crud = token_crud

    def allocate_token(self, token_request):
        now = datetime.now(UTC)

        request_date = (
            token_request.date.date()
            if isinstance(token_request.date, datetime)
            else token_request.date
        )

        incoming_priority = self._priority(token_request.source)

        with self.db.begin():

            # ---------- Explicit slot ----------
            if token_request.slot_id:
                slot = self.slot_crud.get_slot_with_lock(token_request.slot_id)
                if not slot:
                    raise Exception("Slot not found")

                if request_date == now.date() and slot.start_time <= now.time():
                    raise Exception("Slot already started")

                active_tokens = self.token_crud.get_active_tokens_for_slot_ordered(
                    slot.id
                )

                capacity = slot.capacity
                emergency_count = sum(
                    1 for t in active_tokens if t.source == TokenSource.emergency
                )
                capacity += min(emergency_count, settings.max_emergency_overflow)

                # CASE 1: free space
                if len(active_tokens) < capacity:
                    token = Token(
                        doctor_id=token_request.doctor_id,
                        slot_id=slot.id,
                        source=token_request.source,
                        priority=incoming_priority,
                        status=TokenStatus.active,
                    )
                    self.db.add(token)
                    return token

                # CASE 2: try preemption
                lowest = active_tokens[-1]  # worst token

                if incoming_priority < lowest.priority:
                    # displace
                    lowest.status = TokenStatus.displaced
                    lowest.slot_id = None

                    token = Token(
                        doctor_id=token_request.doctor_id,
                        slot_id=slot.id,
                        source=token_request.source,
                        priority=incoming_priority,
                        status=TokenStatus.active,
                    )
                    self.db.add(token)
                    return token

                # CASE 3: reject / wait
                raise Exception("Slot full and higher priority exists")

            # ---------- Auto-assign nearest slot ----------
            slots = self.slot_crud.get_slots_for_doctor_by_date(
                token_request.doctor_id,
                request_date,
            )

            for slot in slots:
                if request_date == now.date() and slot.start_time <= now.time():
                    continue

                locked_slot = self.slot_crud.get_slot_with_lock(slot.id)

                active_tokens = self.token_crud.get_active_tokens_for_slot_ordered(
                    locked_slot.id
                )

                capacity = locked_slot.capacity
                emergency_count = sum(
                    1 for t in active_tokens if t.source == TokenSource.emergency
                )
                capacity += min(emergency_count, settings.max_emergency_overflow)

                if len(active_tokens) < capacity:
                    token = Token(
                        doctor_id=token_request.doctor_id,
                        slot_id=locked_slot.id,
                        source=token_request.source,
                        priority=incoming_priority,
                        status=TokenStatus.active,
                    )
                    self.db.add(token)
                    return token

                # Try preemption in auto mode as well
                lowest = active_tokens[-1]
                if incoming_priority < lowest.priority:
                    lowest.status = TokenStatus.displaced
                    lowest.slot_id = None

                    token = Token(
                        doctor_id=token_request.doctor_id,
                        slot_id=locked_slot.id,
                        source=token_request.source,
                        priority=incoming_priority,
                        status=TokenStatus.active,
                    )
                    self.db.add(token)
                    return token

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

    def _reallocate_for_slot(self, slot_id: str) -> None:
        """
        Reallocate waiting / displaced tokens into a slot.
        Atomic, locked, priority-aware.
        """

        with self.db.begin():

            slot = self.slot_crud.get_slot_with_lock(slot_id)
            if not slot:
                return

            active_tokens = self.token_crud.get_active_tokens_for_slot_ordered(slot_id)

            capacity = slot.capacity
            emergency_count = sum(
                1 for t in active_tokens if t.source == TokenSource.emergency
            )
            capacity += min(emergency_count, settings.max_emergency_overflow)

            available = capacity - len(active_tokens)
            if available <= 0:
                return

            slot_date = slot.date if isinstance(slot.date, date) else slot.date.date()

            # waiting + displaced, ordered by priority then time
            candidates = self.token_crud.get_reallocatable_tokens_for_doctor_by_date(
                slot.doctor_id,
                slot_date,
            )

            for token in candidates:
                if available <= 0:
                    break

                token.slot_id = slot.id
                token.status = TokenStatus.active
                available -= 1

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

    def get_all_slots_for_date(self, date_str: Optional[str]) -> List[Slot]:
            """Get all slots, optionally filtered by date."""
            if date_str:
                try:
                    request_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                except ValueError:
                    raise Exception("Invalid date format. Use YYYY-MM-DD.")
                return self.slot_crud.get_slots_by_date(request_date)
            else:
                return self.slot_crud.get_all_slots()
    
    def get_all_doctors(self) -> List[Doctor]:
        """Get all doctors."""
        return self.doctor_crud.get_all_doctors()
        