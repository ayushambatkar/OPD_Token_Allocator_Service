import random
import time
from datetime import datetime, timedelta, UTC
from app.allocation_service import AllocationService
from app.crud.doctor import DoctorCRUD
from app.crud.slot import SlotCRUD
from app.crud.token import TokenCRUD
from app.db import SessionLocal
from app.models import TokenCreate, TokenSource
from app.schemas import Token


def simulate_opd_day():
    db = SessionLocal()
    try:
        DoctorCRUD.set_db_session(db)
        SlotCRUD.set_db_session(db)
        TokenCRUD.set_db_session(db)

        service = AllocationService(DoctorCRUD(), SlotCRUD(), TokenCRUD())

        doctors = DoctorCRUD().list_doctors()
        sources = list(TokenSource)

        print("Starting OPD day simulation...")

        # Simulate token requests
        for i in range(50):  # 50 token requests
            doctor = random.choice(doctors)
            source = random.choice(sources)
            # Random date between today and next 7 days
            days_ahead = random.randint(0, 7)
            token_date = datetime.now(UTC) + timedelta(days=days_ahead)

            token_request = TokenCreate(
                doctor_id=doctor.id,
                source=source,
                date=token_date,
                patient_name=f"Patient {i+1}",
                patient_contact=f"123456789{i%10}",
            )

            token = service.allocate_token(token_request)
            status = "allocated" if token.status == "active" else "waiting"
            print(f"Token {token.id} for {source.value} - {status}")

            time.sleep(0.1)  # Simulate time

        # Simulate some cancellations and no-shows
        active_tokens = []
        for doctor in doctors:
            tokens = (
                db.query(Token)
                .filter(Token.doctor_id == str(doctor.id), Token.status == "active")
                .all()
            )
            active_tokens.extend(tokens)

        cancel_tokens = random.sample(active_tokens, min(5, len(active_tokens)))
        for token in cancel_tokens:
            service.cancel_token(str(token.id))
            print(f"Cancelled token {token.id}")

        no_show_tokens = random.sample(active_tokens, min(3, len(active_tokens)))
        for token in no_show_tokens:
            service.mark_no_show(str(token.id))
            print(f"No-show token {token.id}")

        # Check waiting lists
        for doctor in doctors:
            today = datetime.now(UTC).date()
            waiting = service.get_waiting_list(str(doctor.id), today)
            print(f"Doctor {doctor.name} has {len(waiting)} waiting tokens for today")

        print("Simulation completed")

    finally:
        db.close()


if __name__ == "__main__":
    simulate_opd_day()
